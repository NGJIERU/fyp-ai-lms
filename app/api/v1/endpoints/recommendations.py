"""
API endpoints for AI Recommendation System
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field

from app import models
from app.api import deps
from app.core.database import get_db
from app.services.recommendation import get_recommendation_engine

router = APIRouter()


# Pydantic schemas for recommendations
class RecommendationItem(BaseModel):
    material_id: int
    title: str
    url: str
    source: str
    type: str
    author: Optional[str]
    description: Optional[str]
    quality_score: float
    similarity_score: float
    combined_score: float

    class Config:
        from_attributes = True


class RecommendationResponse(BaseModel):
    course_id: int
    week_number: int
    topic: str
    recommendations: List[RecommendationItem]


class CourseRecommendationsResponse(BaseModel):
    course_id: int
    weeks: dict  # week_number -> list of recommendations


class PendingApprovalItem(BaseModel):
    mapping_id: int
    material_id: int
    course_id: int
    week_number: int
    relevance_score: float
    material: Optional[dict]


class ApprovalRequest(BaseModel):
    approved: bool = True
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0)


class AutoMapRequest(BaseModel):
    min_similarity: float = Field(0.5, ge=0.3, le=0.9)
    min_quality: float = Field(0.6, ge=0.3, le=0.9)


class AutoMapResponse(BaseModel):
    course_id: int
    mappings_created: int
    message: str


@router.get("/course/{course_id}/week/{week_number}", response_model=RecommendationResponse)
def get_recommendations_for_week(
    course_id: int,
    week_number: int,
    top_k: int = Query(5, ge=1, le=20),
    min_similarity: float = Query(0.3, ge=0.0, le=1.0),
    min_quality: float = Query(0.4, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_lecturer),
):
    """
    Get AI-generated material recommendations for a specific course week.
    Only lecturers and admins can access recommendations.
    """
    # Verify course exists
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check authorization for lecturers
    if current_user.role == models.UserRole.LECTURER and course.lecturer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view recommendations for your own courses"
        )
    
    # Get syllabus to verify week exists
    syllabus = (
        db.query(models.Syllabus)
        .filter(
            models.Syllabus.course_id == course_id,
            models.Syllabus.week_number == week_number,
            models.Syllabus.is_active == True
        )
        .first()
    )
    
    if not syllabus:
        raise HTTPException(
            status_code=404,
            detail=f"No active syllabus found for week {week_number}"
        )
    
    # Get recommendations
    engine = get_recommendation_engine()
    recommendations = engine.recommend_for_topic(
        db=db,
        course_id=course_id,
        week_number=week_number,
        top_k=top_k,
        min_similarity=min_similarity,
        min_quality=min_quality
    )
    
    # Format response
    rec_items = []
    for rec in recommendations:
        mat = rec["material"]
        rec_items.append(RecommendationItem(
            material_id=mat["id"],
            title=mat["title"],
            url=mat["url"],
            source=mat["source"],
            type=mat["type"],
            author=mat.get("author"),
            description=mat.get("description"),
            quality_score=mat["quality_score"],
            similarity_score=rec["similarity_score"],
            combined_score=rec["combined_score"]
        ))
    
    return RecommendationResponse(
        course_id=course_id,
        week_number=week_number,
        topic=syllabus.topic,
        recommendations=rec_items
    )


@router.get("/course/{course_id}", response_model=CourseRecommendationsResponse)
def get_recommendations_for_course(
    course_id: int,
    top_k_per_week: int = Query(5, ge=1, le=10),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_lecturer),
):
    """
    Get AI-generated recommendations for all weeks of a course.
    """
    # Verify course exists and authorization
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if current_user.role == models.UserRole.LECTURER and course.lecturer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view recommendations for your own courses"
        )
    
    engine = get_recommendation_engine()
    all_recommendations = engine.recommend_for_course(
        db=db,
        course_id=course_id,
        top_k_per_week=top_k_per_week
    )
    
    # Format response
    weeks_data = {}
    for week_num, recs in all_recommendations.items():
        weeks_data[week_num] = [
            {
                "material_id": r["material"]["id"],
                "title": r["material"]["title"],
                "similarity_score": r["similarity_score"],
                "quality_score": r["quality_score"],
                "combined_score": r["combined_score"]
            }
            for r in recs
        ]
    
    return CourseRecommendationsResponse(
        course_id=course_id,
        weeks=weeks_data
    )


@router.post("/course/{course_id}/auto-map", response_model=AutoMapResponse)
def auto_map_materials(
    course_id: int,
    request: AutoMapRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_lecturer),
):
    """
    Automatically create material-topic mappings for high-confidence matches.
    Materials are NOT approved by default - lecturer must still review.
    """
    # Verify course exists and authorization
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if current_user.role == models.UserRole.LECTURER and course.lecturer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only auto-map materials for your own courses"
        )
    
    engine = get_recommendation_engine()
    mappings = engine.auto_map_materials(
        db=db,
        course_id=course_id,
        min_similarity=request.min_similarity,
        min_quality=request.min_quality
    )
    
    return AutoMapResponse(
        course_id=course_id,
        mappings_created=len(mappings),
        message=f"Created {len(mappings)} material mappings pending approval"
    )


@router.get("/pending", response_model=List[PendingApprovalItem])
def get_pending_approvals(
    course_id: int = Query(..., description="Course ID"),
    week_number: Optional[int] = Query(None, ge=1, le=14),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_lecturer),
):
    """
    Get materials pending lecturer approval.
    """
    # Verify course exists and authorization
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if current_user.role == models.UserRole.LECTURER and course.lecturer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view pending approvals for your own courses"
        )
    
    engine = get_recommendation_engine()
    pending = engine.get_pending_approvals(
        db=db,
        course_id=course_id,
        week_number=week_number
    )
    
    return [PendingApprovalItem(**p) for p in pending]


@router.post("/approve/{mapping_id}")
def approve_material_mapping(
    mapping_id: int,
    request: ApprovalRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_lecturer),
):
    """
    Approve or reject a material-topic mapping.
    """
    from datetime import datetime
    
    mapping = db.query(models.MaterialTopic).filter(
        models.MaterialTopic.id == mapping_id
    ).first()
    
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    
    # Verify authorization
    course = db.query(models.Course).filter(models.Course.id == mapping.course_id).first()
    if current_user.role == models.UserRole.LECTURER and course.lecturer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only approve materials for your own courses"
        )
    
    if request.approved:
        mapping.approved_by_lecturer = True
        mapping.approved_by = current_user.id
        mapping.approved_at = datetime.utcnow()
        if request.relevance_score is not None:
            mapping.relevance_score = request.relevance_score
        message = "Material approved successfully"
    else:
        # Reject - delete the mapping
        db.delete(mapping)
        message = "Material mapping rejected and removed"
    
    db.commit()
    
    return {"status": "success", "message": message}


@router.post("/update-embeddings")
def trigger_embedding_update(
    batch_size: int = Query(100, ge=10, le=500),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
):
    """
    Trigger embedding update for materials without embeddings.
    Super admin only.
    """
    engine = get_recommendation_engine()
    updated = engine.update_material_embeddings(db=db, batch_size=batch_size)
    
    return {
        "status": "success",
        "materials_updated": updated,
        "message": f"Updated embeddings for {updated} materials"
    }
