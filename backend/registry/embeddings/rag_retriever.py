"""RAG retriever for function discovery with two-stage retrieval."""

import logging
from typing import List, Dict, Any, Optional
import numpy as np

from .sentence_transformer_embedder import SentenceTransformerEmbedder
from .milvus_store import MilvusStore

logger = logging.getLogger(__name__)


class RAGRetriever:
    """
    Two-stage RAG retrieval system:
    1. Vector Search (Milvus) - Get top N candidates
    2. LLM Reranking - Rerank by relevance
    """
    
    def __init__(
        self,
        embedder: SentenceTransformerEmbedder,
        vector_store: MilvusStore,
        initial_top_k: int = 20,
        final_top_k: int = 5
    ):
        """
        Initialize RAG retriever.
        
        Args:
            embedder: Embedder for generating query embeddings
            vector_store: Vector store for similarity search
            initial_top_k: Number of candidates from vector search
            final_top_k: Number of results after reranking
        """
        self.embedder = embedder
        self.vector_store = vector_store
        self.initial_top_k = initial_top_k
        self.final_top_k = final_top_k
    
    def retrieve(
        self,
        query: str,
        category_filter: Optional[str] = None,
        rerank: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant functions for a query.
        
        Args:
            query: User query
            category_filter: Optional category to filter by
            rerank: Whether to rerank results (if False, skip stage 2)
            
        Returns:
            List of relevant functions with scores
        """
        logger.info(f"Retrieving functions for query: {query}")
        
        # Stage 1: Vector Search
        candidates = self._vector_search(query, category_filter)
        
        if not candidates:
            logger.warning("No candidates found in vector search")
            return []
        
        logger.info(f"Vector search found {len(candidates)} candidates")
        
        # Stage 2: LLM Reranking (optional)
        if rerank and len(candidates) > self.final_top_k:
            results = self._rerank(query, candidates)
        else:
            results = candidates[:self.final_top_k]
        
        logger.info(f"Returning {len(results)} results")
        return results
    
    def _vector_search(
        self,
        query: str,
        category_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Stage 1: Vector similarity search.
        
        Args:
            query: User query
            category_filter: Optional category filter
            
        Returns:
            List of candidate functions
        """
        # Generate query embedding
        query_embedding = self.embedder.embed_text(query)
        
        # Build filter expression if category specified
        filter_expr = None
        if category_filter:
            filter_expr = f'category == "{category_filter}"'
        
        # Search vector store
        results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=self.initial_top_k,
            filter_expr=filter_expr
        )
        
        return results
    
    def _rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Stage 2: LLM-based reranking.
        
        Args:
            query: User query
            candidates: Candidate functions from vector search
            
        Returns:
            Reranked list of functions
        """
        # TODO: Implement LLM reranking
        # For now, use a simple heuristic based on:
        # 1. Vector similarity score
        # 2. Query term overlap
        
        scored_candidates = []
        query_terms = set(query.lower().split())
        
        for candidate in candidates:
            # Get vector score
            vector_score = candidate.get("score", 0.0)
            
            # Calculate term overlap score
            func_text = (
                f"{candidate.get('name', '')} "
                f"{candidate.get('description', '')}"
            ).lower()
            func_terms = set(func_text.split())
            
            overlap = len(query_terms.intersection(func_terms))
            overlap_score = overlap / max(len(query_terms), 1)
            
            # Combined score (80% vector, 20% overlap)
            combined_score = 0.8 * vector_score + 0.2 * overlap_score
            
            scored_candidates.append({
                **candidate,
                "rerank_score": combined_score,
                "original_score": vector_score
            })
        
        # Sort by rerank score
        scored_candidates.sort(
            key=lambda x: x["rerank_score"],
            reverse=True
        )
        
        return scored_candidates[:self.final_top_k]
    
    def index_function(self, function_data: Dict[str, Any]) -> None:
        """
        Index a single function.
        
        Args:
            function_data: Function metadata dict
        """
        # Generate embedding
        embedding = self.embedder.embed_function(function_data)
        
        # Insert into vector store
        self.vector_store.insert(
            function_id=str(function_data.get("id")),
            embedding=embedding,
            name=function_data.get("name", ""),
            description=function_data.get("description", ""),
            category=function_data.get("category", "")
        )
        
        logger.debug(f"Indexed function: {function_data.get('name')}")
    
    def index_functions(self, functions: List[Dict[str, Any]]) -> None:
        """
        Index multiple functions in batch.
        
        Args:
            functions: List of function metadata dicts
        """
        if not functions:
            return
        
        logger.info(f"Indexing {len(functions)} functions")
        
        # Generate embeddings
        embeddings = np.array([
            self.embedder.embed_function(func)
            for func in functions
        ])
        
        # Extract metadata
        function_ids = [str(f.get("id")) for f in functions]
        names = [f.get("name", "") for f in functions]
        descriptions = [f.get("description", "") for f in functions]
        categories = [f.get("category", "") for f in functions]
        
        # Insert into vector store
        self.vector_store.insert_batch(
            function_ids=function_ids,
            embeddings=embeddings,
            names=names,
            descriptions=descriptions,
            categories=categories
        )
        
        logger.info("Functions indexed successfully")
    
    def delete_function(self, function_id: str) -> None:
        """Delete a function from the index."""
        self.vector_store.delete_by_function_id(function_id)
        logger.debug(f"Deleted function: {function_id}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get retriever statistics."""
        return {
            "total_functions": self.vector_store.count(),
            "embedding_dimension": self.embedder.dimension,
            "initial_top_k": self.initial_top_k,
            "final_top_k": self.final_top_k
        }
