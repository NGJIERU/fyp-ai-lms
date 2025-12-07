from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app import models, schemas
from app.api import deps
from app.core.database import get_db
from app.services.crawler.manager import CrawlerManager

router = APIRouter()

# Dependency to get CrawlerManager (singleton-ish)
_crawler_manager = CrawlerManager()
# Register crawlers here (e.g., _crawler_manager.register_crawler(YouTubeCrawler()))
# For now, no crawlers are registered.

def get_crawler_manager():
    return _crawler_manager

@router.post("/crawl", response_model=schemas.material.CrawlResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_crawl(
    crawl_request: schemas.material.CrawlRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    manager: CrawlerManager = Depends(get_crawler_manager)
):
    """
    Trigger a background crawl task.
    Only lecturers and super admins can trigger crawls.
    """
    if current_user.role not in [models.UserRole.LECTURER, models.UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only lecturers and admins can trigger crawls"
        )

    # For now, we just mock the trigger or run a dummy if no crawlers
    # In real implementation, we would pass the query from somewhere or iterate all topics
    
    # Example: Run for a specific source
    if crawl_request.crawler_type:
        background_tasks.add_task(
            manager.run_crawler, 
            crawl_request.crawler_type, 
            "python tutorial", # Placeholder query
            crawl_request.max_items
        )
        message = f"Started crawl for {crawl_request.crawler_type}"
    else:
        # Run all registered crawlers
        for source in manager.crawlers:
            background_tasks.add_task(
                manager.run_crawler,
                source,
                "python tutorial", # Placeholder query
                crawl_request.max_items
            )
        message = "Started crawl for all sources"

    return schemas.material.CrawlResponse(
        status="accepted",
        crawler_type=crawl_request.crawler_type or "all",
        items_fetched=0, # Async
        message=message
    )

@router.get("/", response_model=List[schemas.material.MaterialRead])
def list_materials(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    type: Optional[str] = Query(None, description="Filter by material type"),
    source: Optional[str] = Query(None, description="Filter by source"),
    min_quality: Optional[float] = Query(None, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    List materials with optional filtering.
    """
    query = db.query(models.Material)
    
    if type:
        query = query.filter(models.Material.type == type)
    if source:
        query = query.filter(models.Material.source == source)
    if min_quality is not None:
        query = query.filter(models.Material.quality_score >= min_quality)
        
    materials = query.order_by(models.Material.created_at.desc()).offset(skip).limit(limit).all()
    return materials

@router.get("/search", response_model=List[schemas.material.MaterialSearchResult])
def search_materials(
    query: str,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Search materials. 
    Currently uses simple text search. Will be upgraded to vector search later.
    """
    # Simple ILIKE search for now
    search_term = f"%{query}%"
    materials = (
        db.query(models.Material)
        .filter(
            (models.Material.title.ilike(search_term)) | 
            (models.Material.description.ilike(search_term))
        )
        .limit(limit)
        .all()
    )
    
    results = []
    for mat in materials:
        results.append(schemas.material.MaterialSearchResult(
            material=mat,
            similarity_score=0.5, # Mock score
            relevance_score=0.5
        ))
    return results

@router.get("/course/{course_id}/week/{week_number}", response_model=List[schemas.material.MaterialTopicRead])
def get_course_week_materials(
    course_id: int,
    week_number: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Get materials mapped to a specific course week.
    """
    topics = (
        db.query(models.MaterialTopic)
        .filter(
            models.MaterialTopic.course_id == course_id,
            models.MaterialTopic.week_number == week_number
        )
        .all()
    )
    
    # Format response
    results = []
    for topic in topics:
        db.refresh(topic, ['material', 'course'])
        topic_dict = topic.__dict__
        topic_dict['material'] = topic.material
        topic_dict['course_name'] = topic.course.name if topic.course else None
        results.append(schemas.material.MaterialTopicRead(**topic_dict))
        
    return results

@router.post("/{material_id}/approve", response_model=schemas.material.MaterialTopicRead)
def approve_material(
    material_id: int,
    topic_create: schemas.material.MaterialTopicCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_lecturer),
):
    """
    Approve/Map a material to a course week.
    Only lecturers can approve materials.
    """
    # Check if material exists
    material = db.query(models.Material).filter(models.Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
        
    # Check if mapping already exists
    existing = (
        db.query(models.MaterialTopic)
        .filter(
            models.MaterialTopic.material_id == material_id,
            models.MaterialTopic.course_id == topic_create.course_id,
            models.MaterialTopic.week_number == topic_create.week_number
        )
        .first()
    )
    
    if existing:
        # Update existing
        existing.relevance_score = topic_create.relevance_score
        existing.approved_by_lecturer = True
        existing.approved_by = current_user.id
        existing.approved_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        result_topic = existing
    else:
        # Create new mapping
        new_topic = models.MaterialTopic(
            material_id=material_id,
            course_id=topic_create.course_id,
            week_number=topic_create.week_number,
            relevance_score=topic_create.relevance_score,
            approved_by_lecturer=True,
            approved_by=current_user.id,
            approved_at=datetime.utcnow()
        )
        db.add(new_topic)
        db.commit()
        db.refresh(new_topic)
        result_topic = new_topic
        
    db.refresh(result_topic, ['material', 'course'])
    topic_dict = result_topic.__dict__
    topic_dict['material'] = result_topic.material
    topic_dict['course_name'] = result_topic.course.name if result_topic.course else None
    
    return schemas.material.MaterialTopicRead(**topic_dict)
