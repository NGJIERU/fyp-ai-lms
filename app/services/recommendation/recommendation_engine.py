"""
AI Recommendation Engine
Matches crawled materials to weekly syllabus using semantic similarity
Ranks and filters recommendations for lecturer approval
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.material import Material, MaterialTopic
from app.models.syllabus import Syllabus
from app.models.course import Course
from app.services.processing.embedding_service import EmbeddingService, get_embedding_service
from app.services.processing.quality_scorer import QualityScorer, get_quality_scorer

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    AI-powered recommendation engine for matching materials to syllabus topics.
    Uses semantic similarity and quality scoring to rank recommendations.
    """
    
    # Configuration
    DEFAULT_TOP_K = 5
    MIN_SIMILARITY_THRESHOLD = 0.3
    MIN_QUALITY_THRESHOLD = 0.4
    
    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        quality_scorer: Optional[QualityScorer] = None
    ):
        """
        Initialize the recommendation engine.
        
        Args:
            embedding_service: Service for generating embeddings
            quality_scorer: Service for calculating quality scores
        """
        self.embedding_service = embedding_service or get_embedding_service()
        self.quality_scorer = quality_scorer or get_quality_scorer()
    
    def recommend_for_topic(
        self,
        db: Session,
        course_id: int,
        week_number: int,
        top_k: int = DEFAULT_TOP_K,
        min_similarity: float = MIN_SIMILARITY_THRESHOLD,
        min_quality: float = MIN_QUALITY_THRESHOLD,
        exclude_approved: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Generate material recommendations for a specific syllabus topic.
        
        Args:
            db: Database session
            course_id: Course ID
            week_number: Week number (1-14)
            top_k: Number of recommendations to return
            min_similarity: Minimum similarity threshold
            min_quality: Minimum quality score threshold
            exclude_approved: Whether to exclude already approved materials
            
        Returns:
            List of recommendation dictionaries with material and scores
        """
        # Get syllabus entry
        syllabus = (
            db.query(Syllabus)
            .filter(
                Syllabus.course_id == course_id,
                Syllabus.week_number == week_number,
                Syllabus.is_active == True
            )
            .first()
        )
        
        if not syllabus:
            logger.warning(f"No active syllabus found for course {course_id}, week {week_number}")
            return []
        
        # Generate embedding for the topic
        topic_embedding = self.embedding_service.embed_syllabus_topic(
            syllabus.topic,
            syllabus.content or ""
        )
        
        # Get candidate materials
        materials_query = db.query(Material).filter(
            Material.quality_score >= min_quality
        )
        
        # Exclude already approved materials if requested
        if exclude_approved:
            approved_ids = (
                db.query(MaterialTopic.material_id)
                .filter(
                    MaterialTopic.course_id == course_id,
                    MaterialTopic.week_number == week_number,
                    MaterialTopic.approved_by_lecturer == True
                )
                .subquery()
            )
            materials_query = materials_query.filter(
                ~Material.id.in_(approved_ids)
            )
        
        materials = materials_query.all()
        
        if not materials:
            logger.info(f"No candidate materials found for course {course_id}, week {week_number}")
            return []
        
        # Calculate similarities and rank
        recommendations = []
        for material in materials:
            # Get or compute material embedding
            material_embedding = self._get_material_embedding(material)
            
            # Calculate similarity
            similarity = self.embedding_service.compute_similarity(
                topic_embedding,
                material_embedding
            )
            
            if similarity < min_similarity:
                continue
            
            # Calculate combined score
            combined_score = self._calculate_combined_score(
                similarity,
                material.quality_score
            )
            
            recommendations.append({
                "material_id": material.id,
                "material": {
                    "id": material.id,
                    "title": material.title,
                    "url": material.url,
                    "source": material.source,
                    "type": material.type,
                    "author": material.author,
                    "description": material.description,
                    "snippet": material.snippet,
                    "quality_score": material.quality_score,
                },
                "similarity_score": similarity,
                "quality_score": material.quality_score,
                "combined_score": combined_score,
                "course_id": course_id,
                "week_number": week_number,
                "topic": syllabus.topic,
            })
        
        # Sort by combined score
        recommendations.sort(key=lambda x: x["combined_score"], reverse=True)
        
        return recommendations[:top_k]
    
    def recommend_for_course(
        self,
        db: Session,
        course_id: int,
        top_k_per_week: int = DEFAULT_TOP_K
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        Generate recommendations for all weeks of a course.
        
        Args:
            db: Database session
            course_id: Course ID
            top_k_per_week: Number of recommendations per week
            
        Returns:
            Dictionary mapping week numbers to recommendation lists
        """
        # Get all active syllabus entries for the course
        syllabus_entries = (
            db.query(Syllabus)
            .filter(
                Syllabus.course_id == course_id,
                Syllabus.is_active == True
            )
            .order_by(Syllabus.week_number)
            .all()
        )
        
        recommendations = {}
        for entry in syllabus_entries:
            week_recs = self.recommend_for_topic(
                db=db,
                course_id=course_id,
                week_number=entry.week_number,
                top_k=top_k_per_week
            )
            recommendations[entry.week_number] = week_recs
        
        return recommendations
    
    def auto_map_materials(
        self,
        db: Session,
        course_id: int,
        min_similarity: float = 0.5,
        min_quality: float = 0.6
    ) -> List[MaterialTopic]:
        """
        Automatically create material-topic mappings for high-confidence matches.
        These are NOT approved by default - lecturer must still review.
        
        Args:
            db: Database session
            course_id: Course ID
            min_similarity: Higher threshold for auto-mapping
            min_quality: Higher quality threshold
            
        Returns:
            List of created MaterialTopic entries
        """
        created_mappings = []
        
        # Get all weeks
        syllabus_entries = (
            db.query(Syllabus)
            .filter(
                Syllabus.course_id == course_id,
                Syllabus.is_active == True
            )
            .all()
        )
        
        for entry in syllabus_entries:
            recommendations = self.recommend_for_topic(
                db=db,
                course_id=course_id,
                week_number=entry.week_number,
                top_k=10,  # Get more candidates
                min_similarity=min_similarity,
                min_quality=min_quality
            )
            
            for rec in recommendations[:5]:  # Top 5 per week
                # Check if mapping already exists
                existing = (
                    db.query(MaterialTopic)
                    .filter(
                        MaterialTopic.material_id == rec["material_id"],
                        MaterialTopic.course_id == course_id,
                        MaterialTopic.week_number == entry.week_number
                    )
                    .first()
                )
                
                if existing:
                    continue
                
                # Create new mapping (not approved)
                mapping = MaterialTopic(
                    material_id=rec["material_id"],
                    course_id=course_id,
                    week_number=entry.week_number,
                    relevance_score=rec["similarity_score"],
                    approved_by_lecturer=False
                )
                db.add(mapping)
                created_mappings.append(mapping)
        
        db.commit()
        
        for mapping in created_mappings:
            db.refresh(mapping)
        
        logger.info(f"Auto-mapped {len(created_mappings)} materials for course {course_id}")
        return created_mappings
    
    def get_pending_approvals(
        self,
        db: Session,
        course_id: int,
        week_number: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get materials pending lecturer approval.
        
        Args:
            db: Database session
            course_id: Course ID
            week_number: Optional specific week
            
        Returns:
            List of pending material mappings with details
        """
        query = (
            db.query(MaterialTopic)
            .filter(
                MaterialTopic.course_id == course_id,
                MaterialTopic.approved_by_lecturer == False
            )
        )
        
        if week_number:
            query = query.filter(MaterialTopic.week_number == week_number)
        
        pending = query.order_by(
            MaterialTopic.week_number,
            MaterialTopic.relevance_score.desc()
        ).all()
        
        results = []
        for mapping in pending:
            db.refresh(mapping, ['material', 'course'])
            results.append({
                "mapping_id": mapping.id,
                "material_id": mapping.material_id,
                "course_id": mapping.course_id,
                "week_number": mapping.week_number,
                "relevance_score": mapping.relevance_score,
                "material": {
                    "id": mapping.material.id,
                    "title": mapping.material.title,
                    "url": mapping.material.url,
                    "source": mapping.material.source,
                    "type": mapping.material.type,
                    "quality_score": mapping.material.quality_score,
                } if mapping.material else None
            })
        
        return results
    
    def _get_material_embedding(self, material: Material) -> List[float]:
        """
        Get or compute embedding for a material.
        """
        # If embedding is stored, use it
        if material.embedding:
            return material.embedding
        
        # Otherwise, compute it
        material_data = {
            "title": material.title,
            "description": material.description,
            "snippet": material.snippet,
            "content_text": material.content_text,
        }
        return self.embedding_service.embed_material(material_data)
    
    def _calculate_combined_score(
        self,
        similarity: float,
        quality: float,
        similarity_weight: float = 0.6,
        quality_weight: float = 0.4
    ) -> float:
        """
        Calculate combined recommendation score.
        
        Args:
            similarity: Semantic similarity score
            quality: Material quality score
            similarity_weight: Weight for similarity
            quality_weight: Weight for quality
            
        Returns:
            Combined score (0.0 - 1.0)
        """
        return (similarity * similarity_weight) + (quality * quality_weight)
    
    def update_material_embeddings(
        self,
        db: Session,
        batch_size: int = 100
    ) -> int:
        """
        Update embeddings for materials that don't have them.
        
        Args:
            db: Database session
            batch_size: Number of materials to process at once
            
        Returns:
            Number of materials updated
        """
        # Get materials without embeddings
        materials = (
            db.query(Material)
            .filter(Material.embedding == None)
            .limit(batch_size)
            .all()
        )
        
        if not materials:
            return 0
        
        updated = 0
        for material in materials:
            try:
                embedding = self._get_material_embedding(material)
                material.embedding = embedding
                updated += 1
            except Exception as e:
                logger.error(f"Error generating embedding for material {material.id}: {e}")
        
        db.commit()
        logger.info(f"Updated embeddings for {updated} materials")
        return updated


# Singleton instance
_recommendation_engine: Optional[RecommendationEngine] = None


def get_recommendation_engine() -> RecommendationEngine:
    """Get or create the recommendation engine singleton."""
    global _recommendation_engine
    if _recommendation_engine is None:
        _recommendation_engine = RecommendationEngine()
    return _recommendation_engine
