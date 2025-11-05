"""Sentence Transformer embedder for generating function embeddings."""

import logging
from typing import List, Optional
import numpy as np

logger = logging.getLogger(__name__)


class SentenceTransformerEmbedder:
    """Generate embeddings using Sentence Transformers."""
    
    def __init__(
        self, 
        model_name: str = "all-MiniLM-L6-v2",
        device: Optional[str] = None
    ):
        """
        Initialize the embedder.
        
        Args:
            model_name: Name of the sentence-transformers model
            device: Device to use ('cpu', 'cuda', or None for auto-detect)
        """
        self.model_name = model_name
        self.device = device
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the sentence transformer model."""
        try:
            from sentence_transformers import SentenceTransformer
            
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(
                self.model_name,
                device=self.device,
                trust_remote_code=True
            )
            logger.info("Embedding model loaded successfully")
            
        except ImportError:
            logger.error("sentence-transformers not installed")
            raise
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as numpy array
        """
        if not self.model:
            raise RuntimeError("Model not loaded")
        
        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        
        return embedding
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            Array of embedding vectors
        """
        if not self.model:
            raise RuntimeError("Model not loaded")
        
        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=len(texts) > 10
        )
        
        return embeddings
    
    def embed_function(self, function_data: dict) -> np.ndarray:
        """
        Generate embedding for a function using its metadata.
        
        Args:
            function_data: Function metadata dict with keys:
                - name: Function name
                - description: Function description
                - parameters: Function parameters (optional)
                - category: Function category (optional)
                
        Returns:
            Embedding vector
        """
        # Create a rich text representation of the function
        parts = []
        
        if function_data.get("name"):
            parts.append(f"Function: {function_data['name']}")
        
        if function_data.get("description"):
            parts.append(f"Description: {function_data['description']}")
        
        if function_data.get("category"):
            parts.append(f"Category: {function_data['category']}")
        
        if function_data.get("parameters"):
            # Handle both old format (list) and new format (dict)
            params = function_data["parameters"]
            if isinstance(params, dict):
                # New format: Dict[str, ParameterSchema] or Dict[str, dict]
                param_names = list(params.keys())
                params_str = ", ".join(param_names)
            elif isinstance(params, list):
                # Old format: List[dict]
                params_str = ", ".join([
                    p.get("name", "") for p in params
                ])
            else:
                params_str = ""
            
            if params_str:
                parts.append(f"Parameters: {params_str}")
        
        text = " | ".join(parts)
        return self.embed_text(text)
    
    @property
    def dimension(self) -> int:
        """Get the embedding dimension."""
        if not self.model:
            raise RuntimeError("Model not loaded")
        return self.model.get_sentence_embedding_dimension()
