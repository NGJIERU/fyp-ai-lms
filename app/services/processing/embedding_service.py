"""
Embedding Service - Generates vector embeddings for materials and queries
Uses sentence-transformers for local embeddings or OpenAI for cloud embeddings
"""
import os
import logging
from typing import List, Optional, Union
import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating text embeddings.
    Supports both local (sentence-transformers) and cloud (OpenAI) models.
    """
    
    # Recommended models for different use cases
    MODELS = {
        "local_fast": "all-MiniLM-L6-v2",           # Fast, good quality (384 dims)
        "local_accurate": "all-mpnet-base-v2",      # Higher quality (768 dims)
        "local_multilingual": "paraphrase-multilingual-MiniLM-L12-v2",  # Multi-language
        "openai_small": "text-embedding-3-small",   # OpenAI small (1536 dims)
        "openai_large": "text-embedding-3-large",   # OpenAI large (3072 dims)
    }
    
    def __init__(
        self,
        model_name: str = "local_fast",
        use_openai: bool = False,
        openai_api_key: Optional[str] = None
    ):
        """
        Initialize the embedding service.
        
        Args:
            model_name: Model identifier (see MODELS dict)
            use_openai: Whether to use OpenAI embeddings
            openai_api_key: OpenAI API key (optional, uses env var if not provided)
        """
        self.use_openai = use_openai
        self.model_name = self.MODELS.get(model_name, model_name)
        self.model = None
        self.openai_client = None
        
        if use_openai:
            self._init_openai(openai_api_key)
        else:
            self._init_local()
    
    def _init_local(self):
        """Initialize local sentence-transformers model."""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            logger.info(f"Loaded local embedding model: {self.model_name} ({self.embedding_dim} dims)")
        except ImportError:
            logger.error("sentence-transformers not installed. Run: pip install sentence-transformers")
            raise
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
            raise
    
    def _init_openai(self, api_key: Optional[str] = None):
        """Initialize OpenAI embedding client."""
        try:
            from openai import OpenAI
            api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key not provided")
            self.openai_client = OpenAI(api_key=api_key)
            # Set embedding dimension based on model
            if "small" in self.model_name:
                self.embedding_dim = 1536
            else:
                self.embedding_dim = 3072
            logger.info(f"Initialized OpenAI embedding client: {self.model_name}")
        except ImportError:
            logger.error("openai package not installed. Run: pip install openai")
            raise
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {e}")
            raise
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        if not text or not text.strip():
            return [0.0] * self.embedding_dim
        
        # Truncate very long texts
        text = text[:8000]  # Most models have token limits
        
        if self.use_openai:
            return self._embed_openai(text)
        else:
            return self._embed_local(text)
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch processing).
        
        Args:
            texts: List of input texts
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        # Filter and truncate
        processed_texts = [t[:8000] if t and t.strip() else "" for t in texts]
        
        if self.use_openai:
            return self._embed_openai_batch(processed_texts)
        else:
            return self._embed_local_batch(processed_texts)
    
    def _embed_local(self, text: str) -> List[float]:
        """Generate embedding using local model."""
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Local embedding error: {e}")
            return [0.0] * self.embedding_dim
    
    def _embed_local_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for batch using local model."""
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Local batch embedding error: {e}")
            return [[0.0] * self.embedding_dim for _ in texts]
    
    def _embed_openai(self, text: str) -> List[float]:
        """Generate embedding using OpenAI API."""
        try:
            response = self.openai_client.embeddings.create(
                input=text,
                model=self.model_name
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            return [0.0] * self.embedding_dim
    
    def _embed_openai_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for batch using OpenAI API."""
        try:
            # OpenAI has a limit on batch size
            batch_size = 100
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                response = self.openai_client.embeddings.create(
                    input=batch,
                    model=self.model_name
                )
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
            
            return all_embeddings
        except Exception as e:
            logger.error(f"OpenAI batch embedding error: {e}")
            return [[0.0] * self.embedding_dim for _ in texts]
    
    def compute_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (0.0 to 1.0)
        """
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            # Normalize to 0-1 range (cosine can be -1 to 1)
            return float((similarity + 1) / 2)
        except Exception as e:
            logger.error(f"Similarity computation error: {e}")
            return 0.0
    
    def find_most_similar(
        self,
        query_embedding: List[float],
        candidate_embeddings: List[List[float]],
        top_k: int = 5
    ) -> List[tuple]:
        """
        Find the most similar embeddings to a query.
        
        Args:
            query_embedding: Query vector
            candidate_embeddings: List of candidate vectors
            top_k: Number of top results to return
            
        Returns:
            List of (index, similarity_score) tuples, sorted by similarity
        """
        if not candidate_embeddings:
            return []
        
        similarities = []
        for i, candidate in enumerate(candidate_embeddings):
            sim = self.compute_similarity(query_embedding, candidate)
            similarities.append((i, sim))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    def embed_material(self, material_data: dict) -> List[float]:
        """
        Generate embedding for a material by combining relevant fields.
        
        Args:
            material_data: Dictionary with material fields
            
        Returns:
            Embedding vector
        """
        # Combine relevant text fields with weights
        text_parts = []
        
        # Title is most important
        if material_data.get("title"):
            text_parts.append(material_data["title"])
            text_parts.append(material_data["title"])  # Double weight
        
        # Description
        if material_data.get("description"):
            text_parts.append(material_data["description"])
        
        # Content snippet
        if material_data.get("snippet"):
            text_parts.append(material_data["snippet"])
        
        # Full content (truncated)
        if material_data.get("content_text"):
            text_parts.append(material_data["content_text"][:2000])
        
        combined_text = " ".join(text_parts)
        return self.embed_text(combined_text)
    
    def embed_syllabus_topic(self, topic: str, content: str = "") -> List[float]:
        """
        Generate embedding for a syllabus topic.
        
        Args:
            topic: Topic title
            content: Additional content/description
            
        Returns:
            Embedding vector
        """
        text = f"{topic} {topic} {content}"  # Double weight on topic
        return self.embed_text(text)


# Singleton cache for convenience
_embedding_services: dict[tuple[str, bool, Optional[str]], EmbeddingService] = {}


def get_embedding_service(
    model_name: str = "local_fast",
    use_openai: bool = False,
    openai_api_key: Optional[str] = None
) -> EmbeddingService:
    """
    Get or create the embedding service singleton for a given configuration.
    """
    global _embedding_services
    key = (model_name, use_openai, openai_api_key if use_openai else None)
    if key not in _embedding_services:
        _embedding_services[key] = EmbeddingService(
            model_name=model_name,
            use_openai=use_openai,
            openai_api_key=openai_api_key
        )
    return _embedding_services[key]
