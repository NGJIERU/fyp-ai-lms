"""
API endpoints for Super Admin functionality
System management, user management, and analytics
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime, timedelta

from app import models
from app.api import deps
from app.core.database import get_db
from app.core import security
from app.services.crawler.crawler_health import get_crawler_health_service

router = APIRouter()


# ==================== Pydantic Schemas ====================

class UserCreateAdmin(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: models.UserRole = models.UserRole.STUDENT
    is_active: bool = True


class UserUpdateAdmin(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[models.UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SystemStats(BaseModel):
    total_users: int
    users_by_role: Dict[str, int]
    total_courses: int
    total_materials: int
    total_enrollments: int
    active_sessions_today: int


class CrawlLogItem(BaseModel):
    id: int
    crawler_type: str
    status: str
    items_fetched: int
    error_message: Optional[str]
    started_at: datetime
    finished_at: Optional[datetime]


class ActivityLogItem(BaseModel):
    id: int
    user_id: int
    user_email: Optional[str]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[int]
    created_at: datetime


class RecommendationStats(BaseModel):
    total_materials: int
    materials_with_embeddings: int
    total_mappings: int
    approved_mappings: int
    pending_mappings: int
    avg_quality_score: float


# ==================== User Management Endpoints ====================

@router.get("/users", response_model=List[UserResponse])
def list_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    role: Optional[models.UserRole] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
):
    """
    List all users with optional filtering.
    Super admin only.
    """
    query = db.query(models.User)
    
    if role:
        query = query.filter(models.User.role == role)
    if is_active is not None:
        query = query.filter(models.User.is_active == is_active)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (models.User.email.ilike(search_term)) |
            (models.User.full_name.ilike(search_term))
        )
    
    users = query.offset(skip).limit(limit).all()
    
    return [
        UserResponse(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            role=u.role.value,
            is_active=u.is_active
        )
        for u in users
    ]


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user_admin(
    user_in: UserCreateAdmin,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
):
    """
    Create a new user. Super admin only.
    """
    # Check if email exists
    existing = db.query(models.User).filter(models.User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists"
        )
    
    user = models.User(
        email=user_in.email,
        hashed_password=security.get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role,
        is_active=user_in.is_active
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        is_active=user.is_active
    )


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user_admin(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
):
    """
    Get a specific user by ID. Super admin only.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        is_active=user.is_active
    )


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user_admin(
    user_id: int,
    user_in: UserUpdateAdmin,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
):
    """
    Update a user. Super admin only.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent self-demotion
    if user.id == current_user.id and user_in.role and user_in.role != models.UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role"
        )
    
    if user_in.email is not None:
        # Check email uniqueness
        existing = db.query(models.User).filter(
            models.User.email == user_in.email,
            models.User.id != user_id
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Email already in use")
        user.email = user_in.email
    
    if user_in.full_name is not None:
        user.full_name = user_in.full_name
    if user_in.role is not None:
        user.role = user_in.role
    if user_in.is_active is not None:
        user.is_active = user_in.is_active
    if user_in.password is not None:
        user.hashed_password = security.get_password_hash(user_in.password)
    
    db.commit()
    db.refresh(user)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        is_active=user.is_active
    )


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_admin(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
):
    """
    Delete a user. Super admin only.
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    return None


# ==================== System Statistics Endpoints ====================

@router.get("/stats", response_model=SystemStats)
def get_system_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
):
    """
    Get system-wide statistics. Super admin only.
    """
    # User counts
    total_users = db.query(models.User).count()
    
    users_by_role = {}
    for role in models.UserRole:
        count = db.query(models.User).filter(models.User.role == role).count()
        users_by_role[role.value] = count
    
    # Course count
    total_courses = db.query(models.Course).count()
    
    # Material count
    total_materials = db.query(models.Material).count()
    
    # Enrollment count
    total_enrollments = db.query(models.StudentEnrollment).filter(
        models.StudentEnrollment.is_active == True
    ).count()
    
    # Active sessions today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    active_sessions = db.query(models.LearningSession).filter(
        models.LearningSession.started_at >= today_start
    ).count()
    
    return SystemStats(
        total_users=total_users,
        users_by_role=users_by_role,
        total_courses=total_courses,
        total_materials=total_materials,
        total_enrollments=total_enrollments,
        active_sessions_today=active_sessions
    )


@router.get("/stats/recommendations", response_model=RecommendationStats)
def get_recommendation_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
):
    """
    Get AI recommendation system statistics. Super admin only.
    """
    total_materials = db.query(models.Material).count()
    
    # Materials with embeddings
    materials_with_embeddings = db.query(models.Material).filter(
        models.Material.embedding != None
    ).count()
    
    # Mapping counts
    total_mappings = db.query(models.MaterialTopic).count()
    approved_mappings = db.query(models.MaterialTopic).filter(
        models.MaterialTopic.approved_by_lecturer == True
    ).count()
    pending_mappings = total_mappings - approved_mappings
    
    # Average quality score
    avg_quality = db.query(func.avg(models.Material.quality_score)).scalar() or 0
    
    return RecommendationStats(
        total_materials=total_materials,
        materials_with_embeddings=materials_with_embeddings,
        total_mappings=total_mappings,
        approved_mappings=approved_mappings,
        pending_mappings=pending_mappings,
        avg_quality_score=round(avg_quality, 3)
    )


# ==================== Crawl Logs Endpoints ====================

@router.get("/crawl-logs", response_model=List[CrawlLogItem])
def get_crawl_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
    crawler_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
):
    """
    Get crawl logs. Super admin only.
    """
    query = db.query(models.CrawlLog)
    
    if status:
        query = query.filter(models.CrawlLog.status == status)
    if crawler_type:
        query = query.filter(models.CrawlLog.crawler_type == crawler_type)
    
    logs = query.order_by(desc(models.CrawlLog.started_at)).offset(skip).limit(limit).all()
    
    return [
        CrawlLogItem(
            id=log.id,
            crawler_type=log.crawler_type,
            status=log.status,
            items_fetched=log.items_fetched,
            error_message=log.error_message,
            started_at=log.started_at,
            finished_at=log.finished_at
        )
        for log in logs
    ]


# ==================== Activity Logs Endpoints ====================

@router.get("/activity-logs", response_model=List[ActivityLogItem])
def get_activity_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
):
    """
    Get activity logs. Super admin only.
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    query = db.query(models.ActivityLog).filter(
        models.ActivityLog.created_at >= cutoff
    )
    
    if user_id:
        query = query.filter(models.ActivityLog.user_id == user_id)
    if action:
        query = query.filter(models.ActivityLog.action == action)
    
    logs = query.order_by(desc(models.ActivityLog.created_at)).offset(skip).limit(limit).all()
    
    result = []
    for log in logs:
        user = db.query(models.User).filter(models.User.id == log.user_id).first()
        result.append(ActivityLogItem(
            id=log.id,
            user_id=log.user_id,
            user_email=user.email if user else None,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            created_at=log.created_at
        ))
    
    return result


# ==================== Course Management Endpoints ====================

@router.get("/courses/all", response_model=List[Dict[str, Any]])
def get_all_courses_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
):
    """
    Get all courses with detailed stats. Super admin only.
    """
    courses = db.query(models.Course).offset(skip).limit(limit).all()
    
    result = []
    for course in courses:
        # Get lecturer
        lecturer = None
        if course.lecturer_id:
            lecturer = db.query(models.User).filter(models.User.id == course.lecturer_id).first()
        
        # Get stats
        enrollments = db.query(models.StudentEnrollment).filter(
            models.StudentEnrollment.course_id == course.id,
            models.StudentEnrollment.is_active == True
        ).count()
        
        materials = db.query(models.MaterialTopic).filter(
            models.MaterialTopic.course_id == course.id,
            models.MaterialTopic.approved_by_lecturer == True
        ).count()
        
        syllabus_weeks = db.query(models.Syllabus).filter(
            models.Syllabus.course_id == course.id,
            models.Syllabus.is_active == True
        ).count()
        
        result.append({
            "id": course.id,
            "code": course.code,
            "name": course.name,
            "description": course.description,
            "lecturer_id": course.lecturer_id,
            "lecturer_name": lecturer.full_name if lecturer else None,
            "enrolled_students": enrollments,
            "approved_materials": materials,
            "syllabus_weeks": syllabus_weeks,
            "is_active": course.is_active,
            "created_at": course.created_at.isoformat() if course.created_at else None
        })
    
    return result


@router.post("/courses/{course_id}/assign-lecturer")
def assign_lecturer_to_course(
    course_id: int,
    lecturer_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
):
    """
    Assign a lecturer to a course. Super admin only.
    """
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    lecturer = db.query(models.User).filter(
        models.User.id == lecturer_id,
        models.User.role.in_([models.UserRole.LECTURER, models.UserRole.SUPER_ADMIN])
    ).first()
    if not lecturer:
        raise HTTPException(status_code=404, detail="Lecturer not found")
    
    course.lecturer_id = lecturer_id
    db.commit()
    
    return {
        "message": "Lecturer assigned successfully",
        "course_id": course_id,
        "lecturer_id": lecturer_id
    }


# ==================== Crawler Health Endpoints ====================

@router.get("/crawler/health")
def get_crawler_health(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_super_admin),
):
    """
    Get crawler health summary.
    Shows overall health score, recent crawl stats, and per-crawler metrics.
    Super admin only.
    """
    health_service = get_crawler_health_service(db)
    return health_service.get_health_summary()


@router.get("/crawler/logs")
def get_crawler_logs(
    crawler_type: Optional[str] = Query(None, description="Filter by crawler type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_super_admin),
):
    """
    Get recent crawler logs with optional filters.
    Super admin only.
    """
    health_service = get_crawler_health_service(db)
    return {
        "logs": health_service.get_recent_logs(
            crawler_type=crawler_type,
            status=status,
            limit=limit
        )
    }


@router.get("/crawler/stats/{crawler_type}")
def get_crawler_stats(
    crawler_type: str,
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_super_admin),
):
    """
    Get detailed stats for a specific crawler.
    Super admin only.
    """
    health_service = get_crawler_health_service(db)
    return health_service.get_crawler_stats(crawler_type, days)
