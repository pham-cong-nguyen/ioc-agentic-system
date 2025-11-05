"""Milvus vector store for function embeddings."""

import logging
from typing import List, Dict, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)


class MilvusStore:
    """Vector store using Milvus for function embeddings."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 19530,
        collection_name: str = "function_embeddings",
        dimension: int = 384  # Default for all-MiniLM-L6-v2
    ):
        """
        Initialize Milvus store.
        
        Args:
            host: Milvus server host
            port: Milvus server port
            collection_name: Name of the collection to use
            dimension: Embedding dimension
        """
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.dimension = dimension
        self.collection = None
        self._connect()
    
    def _connect(self):
        """Connect to Milvus and initialize collection."""
        try:
            from pymilvus import (
                connections,
                Collection,
                CollectionSchema,
                FieldSchema,
                DataType,
                utility
            )
            
            logger.info(f"Connecting to Milvus at {self.host}:{self.port}")
            connections.connect(
                alias="default",
                host=self.host,
                port=self.port
            )
            logger.info("Connected to Milvus successfully")
            
            # Check if collection exists
            if utility.has_collection(self.collection_name):
                logger.info(f"Loading existing collection: {self.collection_name}")
                self.collection = Collection(self.collection_name)
            else:
                logger.info(f"Creating new collection: {self.collection_name}")
                self._create_collection()
            
            # Load collection into memory
            self.collection.load()
            logger.info("Collection loaded into memory")
            
        except ImportError:
            logger.error("pymilvus not installed")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            raise
    
    def _create_collection(self):
        """Create a new collection for function embeddings."""
        from pymilvus import (
            Collection,
            CollectionSchema,
            FieldSchema,
            DataType
        )
        
        # Define schema
        fields = [
            FieldSchema(
                name="id",
                dtype=DataType.INT64,
                is_primary=True,
                auto_id=True
            ),
            FieldSchema(
                name="function_id",
                dtype=DataType.VARCHAR,
                max_length=255
            ),
            FieldSchema(
                name="embedding",
                dtype=DataType.FLOAT_VECTOR,
                dim=self.dimension
            ),
            FieldSchema(
                name="name",
                dtype=DataType.VARCHAR,
                max_length=500
            ),
            FieldSchema(
                name="description",
                dtype=DataType.VARCHAR,
                max_length=2000
            ),
            FieldSchema(
                name="category",
                dtype=DataType.VARCHAR,
                max_length=200
            )
        ]
        
        schema = CollectionSchema(
            fields=fields,
            description="Function embeddings for RAG retrieval"
        )
        
        self.collection = Collection(
            name=self.collection_name,
            schema=schema
        )
        
        # Create IVF_FLAT index for similarity search
        index_params = {
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128}
        }
        
        self.collection.create_index(
            field_name="embedding",
            index_params=index_params
        )
        
        logger.info("Collection created with index")
    
    def insert(
        self,
        function_id: str,
        embedding: np.ndarray,
        name: str,
        description: str,
        category: str = ""
    ) -> Dict[str, Any]:
        """
        Insert a function embedding.
        
        Args:
            function_id: Unique function identifier
            embedding: Embedding vector
            name: Function name
            description: Function description
            category: Function category
            
        Returns:
            Insert result
        """
        if self.collection is None:
            raise RuntimeError("Collection not initialized")
        
        # Ensure embedding is the right shape
        if isinstance(embedding, np.ndarray):
            embedding = embedding.tolist()
        
        entities = [
            [function_id],
            [embedding],
            [name],
            [description],
            [category]
        ]
        
        result = self.collection.insert(entities)
        self.collection.flush()
        
        logger.debug(f"Inserted function: {name} (ID: {function_id})")
        return result
    
    def insert_batch(
        self,
        function_ids: List[str],
        embeddings: np.ndarray,
        names: List[str],
        descriptions: List[str],
        categories: List[str]
    ) -> Dict[str, Any]:
        """
        Insert multiple function embeddings.
        
        Args:
            function_ids: List of function identifiers
            embeddings: Array of embeddings
            names: List of function names
            descriptions: List of function descriptions
            categories: List of function categories
            
        Returns:
            Insert result
        """
        if self.collection is None:
            raise RuntimeError("Collection not initialized")
        
        # Convert embeddings to list format
        if isinstance(embeddings, np.ndarray):
            embeddings = embeddings.tolist()
        
        entities = [
            function_ids,
            embeddings,
            names,
            descriptions,
            categories
        ]
        
        result = self.collection.insert(entities)
        self.collection.flush()
        
        logger.info(f"Inserted {len(function_ids)} functions")
        return result
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        filter_expr: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar functions.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            filter_expr: Optional filter expression
            
        Returns:
            List of search results with scores
        """
        if self.collection is None:
            raise RuntimeError("Collection not initialized")
        
        # Convert to list if numpy array
        if isinstance(query_embedding, np.ndarray):
            query_embedding = query_embedding.tolist()
        
        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 10}
        }
        
        results = self.collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            expr=filter_expr,
            output_fields=["function_id", "name", "description", "category"]
        )
        
        # Format results
        formatted_results = []
        for hits in results:
            for hit in hits:
                formatted_results.append({
                    "function_id": hit.entity.get("function_id"),
                    "name": hit.entity.get("name"),
                    "description": hit.entity.get("description"),
                    "category": hit.entity.get("category"),
                    "score": hit.score
                })
        
        logger.debug(f"Found {len(formatted_results)} similar functions")
        return formatted_results
    
    def delete_by_function_id(self, function_id: str):
        """Delete a function by its ID."""
        if self.collection is None:
            raise RuntimeError("Collection not initialized")
        
        expr = f'function_id == "{function_id}"'
        self.collection.delete(expr)
        self.collection.flush()
        
        logger.debug(f"Deleted function: {function_id}")
    
    def clear(self):
        """Clear all data from the collection."""
        if self.collection is None:
            raise RuntimeError("Collection not initialized")
        
        from pymilvus import utility
        
        self.collection.release()
        utility.drop_collection(self.collection_name)
        self._create_collection()
        self.collection.load()
        
        logger.info("Collection cleared")
    
    def count(self) -> int:
        """Get the number of entities in the collection."""
        if self.collection is None:
            raise RuntimeError("Collection not initialized")
        
        return self.collection.num_entities
