"""
Embedding Cache - LRU cache wrapper for embedding service
Reduces redundant embedding computations by caching in memory and database
"""
import logging
import hashlib
from typing import List, Optional, Dict, Any
from functools import lru_cache
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.services.processing.embedding_service import EmbeddingService, get_embedding_service
from app.models.material import Material

logger = logging.getLogger(__name__)


class EmbeddingCache:
    """
    Caching layer for embeddings.
    Uses in-memory LRU cache + database persistence.
    """
    
    # Cache configuration
    MEMORY_CACHE_SIZE = 1000  # Max items in memory
    CACHE_TTL_HOURS = 24  # Not used for in-memory, but useful for future Redis integration
    
    def __init__(self, embedding_service: Optional[EmbeddingService] = None):
        """
        Initialize the embedding cache.
        
        Args:
            embedding_service: The underlying embedding service to use
        """
        self.embedding_service = embedding_service or get_embedding_service()
        self._memory_cache: Dict[str, List[float]] = {}
        self._cache_hits = 0
        self._cache_misses = 0
    
    def _generate_cache_key(self, text: str) -> str:
        """Generate a cache key from text content."""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def get_embedding(self, text: str, use_cache: bool = True) -> List[float]:
        """
        Get embedding for text, using cache if available.
        
        Args:
            text: Text to embed
            use_cache: Whether to use caching (default True)
            
        Returns:
            Embedding vector
        """
        if not use_cache:
            return self.embedding_service.embed_text(text)
        
        cache_key = self._generate_cache_key(text)
        
        # Check memory cache
        if cache_key in self._memory_cache:
            self._cache_hits += 1
            logger.debug(f"Embedding cache hit (memory): {cache_key[:8]}...")
            return self._memory_cache[cache_key]
        
        # Cache miss - compute embedding
        self._cache_misses += 1
        embedding = self.embedding_service.embed_text(text)
        
        # Store in memory cache (with size limit)
        if len(self._memory_cache) >= self.MEMORY_CACHE_SIZE:
            # Remove oldest entry (simple FIFO, not true LRU)
            oldest_key = next(iter(self._memory_cache))
            del self._memory_cache[oldest_key]
        
        self._memory_cache[cache_key] = embedding
        logger.debug(f"Embedding cached (memory): {cache_key[:8]}...")
        
        return embedding
    
    def get_material_embedding(
        self,
        material: Material,
        db: Optional[Session] = None,
        persist: bool = True
    ) -> List[float]:
        """
        Get embedding for a material, checking database first.
        
        Args:
            material: Material model instance
            db: Database session (required for persistence)
            persist: Whether to save computed embeddings to database
            
        Returns:
            Embedding vector
        """
        # Check if material already has embedding in database
        if material.embedding:
            logger.debug(f"Embedding found in database for material {material.id}")
            return material.embedding
        
        # Generate text for embedding
        text_parts = []
        if material.title:
            text_parts.append(material.title)
            text_parts.append(material.title)  # Double weight
        if material.description:
            text_parts.append(material.description)
        if material.snippet:
            text_parts.append(material.snippet)
        if material.content_text:
            text_parts.append(material.content_text[:2000])
        
        combined_text = " ".join(text_parts)
        
        # Get embedding (using memory cache)
        embedding = self.get_embedding(combined_text)
        
        # Persist to database if requested
        if persist and db:
            try:
                material.embedding = embedding
                db.add(material)
                db.commit()
                logger.debug(f"Embedding persisted to database for material {material.id}")
            except Exception as e:
                logger.warning(f"Failed to persist embedding for material {material.id}: {e}")
                db.rollback()
        
        return embedding
    
    def get_syllabus_embedding(self, topic: str, content: str = "") -> List[float]:
        """
        Get embedding for a syllabus topic.
        
        Args:
            topic: Topic title
            content: Additional content
            
        Returns:
            Embedding vector
        """
        text = f"{topic} {topic} {content}"  # Double weight on topic
        return self.get_embedding(text)
    
    def compute_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """Compute cosine similarity between two embeddings."""
        return self.embedding_service.compute_similarity(embedding1, embedding2)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self._cache_hits + self._cache_misses
        hit_rate = self._cache_hits / total if total > 0 else 0.0
        
        return {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate": round(hit_rate * 100, 2),
            "memory_cache_size": len(self._memory_cache),
            "max_cache_size": self.MEMORY_CACHE_SIZE,
        }
    
    def clear_cache(self):
        """Clear the in-memory cache."""
        self._memory_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
        logger.info("Embedding cache cleared")
    
    def preload_materials(self, db: Session, limit: int = 100):
        """
        Preload embeddings for materials that don't have them.
        
        Args:
            db: Database session
            limit: Maximum number of materials to process
        """
        materials = (
            db.query(Material)
            .filter(Material.embedding == None)
            .limit(limit)
            .all()
        )
        
        processed = 0
        for material in materials:
            try:
                self.get_material_embedding(material, db, persist=True)
                processed += 1
            except Exception as e:
                logger.error(f"Error preloading embedding for material {material.id}: {e}")
        
        logger.info(f"Preloaded embeddings for {processed} materials")
        return processed


# Singleton instance
_embedding_cache: Optional[EmbeddingCache] = None


def get_embedding_cache() -> EmbeddingCache:
    """Get or create the embedding cache singleton."""
    global _embedding_cache
    if _embedding_cache is None:
        _embedding_cache = EmbeddingCache()
    return _embedding_cache
