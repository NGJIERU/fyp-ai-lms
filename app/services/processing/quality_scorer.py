"""
Quality Scorer - Calculates and updates quality scores for materials
Combines multiple signals: domain authority, popularity, recency, relevance
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class QualityScorer:
    """
    Service for calculating material quality scores.
    Combines multiple signals into a unified score (0.0 - 1.0).
    """
    
    # Domain authority scores for known sources
    DOMAIN_AUTHORITY = {
        # Academic institutions
        "MIT OCW": 0.95,
        "Stanford": 0.95,
        "Harvard": 0.95,
        "Berkeley": 0.90,
        "NPTEL": 0.85,
        "Coursera": 0.80,
        "edX": 0.80,
        
        # Tech companies
        "Google": 0.90,
        "Microsoft": 0.90,
        "OpenAI": 0.90,
        "Meta": 0.85,
        "Amazon": 0.85,
        
        # Developer platforms
        "GitHub": 0.75,
        "YouTube": 0.60,  # Base score, adjusted by channel
        "Medium": 0.50,
        "Dev.to": 0.55,
        
        # Academic sources
        "arXiv": 0.85,
        "IEEE": 0.90,
        "ACM": 0.90,
        "Springer": 0.85,
        
        # Educational channels
        "freeCodeCamp.org": 0.85,
        "3Blue1Brown": 0.90,
        "Sentdex": 0.80,
        "Corey Schafer": 0.80,
        "StatQuest": 0.85,
    }
    
    # Weight configuration for different scoring components
    DEFAULT_WEIGHTS = {
        "domain_authority": 0.25,
        "popularity": 0.20,
        "recency": 0.15,
        "content_quality": 0.25,
        "relevance": 0.15,
    }
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        Initialize the quality scorer.
        
        Args:
            weights: Custom weights for scoring components
        """
        self.weights = weights or self.DEFAULT_WEIGHTS
        # Normalize weights to sum to 1.0
        total = sum(self.weights.values())
        self.weights = {k: v / total for k, v in self.weights.items()}
    
    def calculate_score(
        self,
        material_data: Dict[str, Any],
        relevance_score: Optional[float] = None
    ) -> float:
        """
        Calculate overall quality score for a material.
        
        Args:
            material_data: Dictionary with material fields
            relevance_score: Optional pre-computed relevance score
            
        Returns:
            Quality score (0.0 - 1.0)
        """
        scores = {}
        
        # Domain authority
        scores["domain_authority"] = self._score_domain_authority(material_data)
        
        # Popularity
        scores["popularity"] = self._score_popularity(material_data)
        
        # Recency
        scores["recency"] = self._score_recency(material_data)
        
        # Content quality
        scores["content_quality"] = self._score_content_quality(material_data)
        
        # Relevance (if provided)
        scores["relevance"] = relevance_score if relevance_score is not None else 0.5
        
        # Weighted sum
        final_score = sum(
            scores[component] * self.weights[component]
            for component in self.weights
        )
        
        return min(max(final_score, 0.0), 1.0)
    
    def _score_domain_authority(self, material_data: Dict[str, Any]) -> float:
        """Score based on source domain authority."""
        source = material_data.get("source", "")
        author = material_data.get("author", "")
        
        # Check source
        for domain, score in self.DOMAIN_AUTHORITY.items():
            if domain.lower() in source.lower():
                return score
        
        # Check author/channel
        for domain, score in self.DOMAIN_AUTHORITY.items():
            if domain.lower() in author.lower():
                return score
        
        # Default score for unknown sources
        return 0.4
    
    def _score_popularity(self, material_data: Dict[str, Any]) -> float:
        """Score based on popularity metrics."""
        metadata = material_data.get("metadata", {})
        
        # Different metrics for different types
        material_type = material_data.get("type", "")
        
        if material_type == "video":
            view_count = metadata.get("view_count", 0)
            like_count = metadata.get("like_count", 0)
            
            # View count scoring
            if view_count > 1000000:
                view_score = 1.0
            elif view_count > 100000:
                view_score = 0.8
            elif view_count > 10000:
                view_score = 0.6
            elif view_count > 1000:
                view_score = 0.4
            else:
                view_score = 0.2
            
            # Like ratio
            if view_count > 0 and like_count > 0:
                like_ratio = like_count / view_count
                like_score = min(like_ratio * 20, 1.0)  # 5% ratio = 1.0
            else:
                like_score = 0.3
            
            return (view_score * 0.6 + like_score * 0.4)
        
        elif material_type == "repository":
            stars = metadata.get("stars", 0)
            forks = metadata.get("forks", 0)
            
            # Star scoring
            if stars > 10000:
                star_score = 1.0
            elif stars > 1000:
                star_score = 0.8
            elif stars > 100:
                star_score = 0.6
            elif stars > 10:
                star_score = 0.4
            else:
                star_score = 0.2
            
            # Fork scoring
            if forks > 1000:
                fork_score = 1.0
            elif forks > 100:
                fork_score = 0.7
            elif forks > 10:
                fork_score = 0.4
            else:
                fork_score = 0.2
            
            return (star_score * 0.7 + fork_score * 0.3)
        
        elif material_type == "article":
            # For academic papers, use citation count if available
            citations = metadata.get("citation_count", 0)
            if citations > 100:
                return 1.0
            elif citations > 50:
                return 0.8
            elif citations > 10:
                return 0.6
            elif citations > 0:
                return 0.4
            else:
                return 0.5  # Default for papers without citation data
        
        # Default for other types
        return 0.5
    
    def _score_recency(self, material_data: Dict[str, Any]) -> float:
        """Score based on how recent the content is."""
        publish_date = material_data.get("publish_date")
        metadata = material_data.get("metadata", {})
        
        # Try to get date from various sources
        if not publish_date:
            publish_date = metadata.get("last_updated")
        
        if not publish_date:
            return 0.5  # Default for unknown dates
        
        # Handle string dates
        if isinstance(publish_date, str):
            try:
                publish_date = datetime.fromisoformat(publish_date.replace("Z", "+00:00"))
            except ValueError:
                return 0.5
        
        # Make datetime offset-naive for comparison
        if publish_date.tzinfo is not None:
            publish_date = publish_date.replace(tzinfo=None)
        
        days_old = (datetime.now() - publish_date).days
        
        # Scoring based on age
        if days_old < 30:
            return 1.0
        elif days_old < 90:
            return 0.9
        elif days_old < 180:
            return 0.8
        elif days_old < 365:
            return 0.7
        elif days_old < 730:
            return 0.5
        elif days_old < 1825:  # 5 years
            return 0.3
        else:
            return 0.2
    
    def _score_content_quality(self, material_data: Dict[str, Any]) -> float:
        """Score based on content quality indicators."""
        score = 0.0
        
        # Title quality
        title = material_data.get("title", "")
        if title:
            # Longer, descriptive titles are better
            if len(title) > 50:
                score += 0.15
            elif len(title) > 20:
                score += 0.1
            
            # Educational keywords
            educational_keywords = [
                "tutorial", "guide", "introduction", "learn",
                "course", "complete", "comprehensive", "beginner",
                "advanced", "fundamentals", "explained"
            ]
            if any(kw in title.lower() for kw in educational_keywords):
                score += 0.1
        
        # Description quality
        description = material_data.get("description", "")
        if description:
            if len(description) > 500:
                score += 0.2
            elif len(description) > 200:
                score += 0.15
            elif len(description) > 50:
                score += 0.1
        
        # Content availability
        content_text = material_data.get("content_text", "")
        if content_text:
            if len(content_text) > 5000:
                score += 0.25
            elif len(content_text) > 1000:
                score += 0.2
            elif len(content_text) > 200:
                score += 0.1
        
        # Metadata completeness
        metadata = material_data.get("metadata", {})
        if metadata:
            # Has transcript (for videos)
            if metadata.get("has_transcript"):
                score += 0.15
            # Has README (for repos)
            if metadata.get("has_readme"):
                score += 0.1
            # Has topics/tags
            if metadata.get("topics") and len(metadata["topics"]) >= 3:
                score += 0.1
        
        # Author information
        if material_data.get("author"):
            score += 0.05
        
        return min(score, 1.0)
    
    def batch_calculate_scores(
        self,
        materials: List[Dict[str, Any]],
        relevance_scores: Optional[List[float]] = None
    ) -> List[float]:
        """
        Calculate quality scores for multiple materials.
        
        Args:
            materials: List of material dictionaries
            relevance_scores: Optional list of relevance scores
            
        Returns:
            List of quality scores
        """
        if relevance_scores is None:
            relevance_scores = [None] * len(materials)
        
        return [
            self.calculate_score(material, relevance)
            for material, relevance in zip(materials, relevance_scores)
        ]
    
    def get_score_breakdown(self, material_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Get detailed breakdown of quality score components.
        
        Args:
            material_data: Dictionary with material fields
            
        Returns:
            Dictionary with individual component scores
        """
        return {
            "domain_authority": self._score_domain_authority(material_data),
            "popularity": self._score_popularity(material_data),
            "recency": self._score_recency(material_data),
            "content_quality": self._score_content_quality(material_data),
            "weights": self.weights.copy(),
        }


# Singleton instance
_quality_scorer: Optional[QualityScorer] = None


def get_quality_scorer() -> QualityScorer:
    """Get or create the quality scorer singleton."""
    global _quality_scorer
    if _quality_scorer is None:
        _quality_scorer = QualityScorer()
    return _quality_scorer
