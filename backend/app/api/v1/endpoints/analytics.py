"""
API endpoints for Analytics and Tracking
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel

from app import models
from app.api import deps
from app.core.database import get_db

router = APIRouter()

class HeartbeatRequest(BaseModel):
    course_id: Optional[int] = None
    page_url: Optional[str] = None

class HeartbeatResponse(BaseModel):
    session_id: int
    duration_seconds: int
    status: str

@router.post("/heartbeat", response_model=HeartbeatResponse)
def record_heartbeat(
    heartbeat: HeartbeatRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Record a heartbeat to track study time.
    Updates existing session if active within last 5 minutes, else starts new one.
    """
    # Only track students
    if current_user.role not in [models.UserRole.STUDENT, models.UserRole.SUPER_ADMIN]:
        return HeartbeatResponse(session_id=0, duration_seconds=0, status="ignored")

    now = datetime.now(timezone.utc)
    five_mins_ago = now - timedelta(minutes=5)

    # Find active session (updated recently)
    active_session = (
        db.query(models.LearningSession)
        .filter(
            models.LearningSession.student_id == current_user.id,
            models.LearningSession.ended_at >= five_mins_ago
        )
        .order_by(models.LearningSession.ended_at.desc())
        .first()
    )

    if active_session:
        # Extend existing session
        active_session.ended_at = now
        
        # Update course if provided and different (simple logic: last course wins for the session context)
        if heartbeat.course_id:
            active_session.course_id = heartbeat.course_id
            
        # Update duration
        duration = (active_session.ended_at - active_session.started_at).total_seconds()
        active_session.duration_seconds = int(duration)
        
        db.commit()
        return HeartbeatResponse(
            session_id=active_session.id, 
            duration_seconds=active_session.duration_seconds, 
            status="extended"
        )
    else:
        # Start new session
        # If no course_id provided, try to find one from enrollments or default to 0/None
        course_id = heartbeat.course_id
        if not course_id:
            # Fallback: assign to first enrolled course or keep None if nullable
            # Detailed implementation might differ, here we handle nullable course_id if model allows,
            # but model defines course_id as ForeignKey usually nullable=False.
            # Let's check model definition.
            # Reviewing `models/performance.py`, LearningSession.course_id IS nullable=False.
            # So we MUST provide a course_id.
            
            # Find any active enrollment
            enrollment = (
                db.query(models.StudentEnrollment)
                .filter(models.StudentEnrollment.student_id == current_user.id)
                .first()
            )
            if enrollment:
                course_id = enrollment.course_id
            else:
                # Edge case: Student has no courses.
                # Use a dummy ID 1 or skip tracking? 
                # Better to skip tracking if we can't link to a course, OR change model to allow nullable.
                # Changing model is risky. Let's assume we need a valid course_id.
                # If we really can't find one, we might fail or need a 'General' course.
                # For now, if no course provided and no enrollments, we return ignored.
                return HeartbeatResponse(session_id=0, duration_seconds=0, status="no_course_context")

        new_session = models.LearningSession(
            student_id=current_user.id,
            course_id=course_id,
            session_type="self_study", # Default type
            started_at=now,
            ended_at=now,
            duration_seconds=0,
            interactions_count=0
        )
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        
        return HeartbeatResponse(
            session_id=new_session.id, 
            duration_seconds=0, 
            status="started"
        )

class ActivityLogRequest(BaseModel):
    action: str
    resource_type: str
    resource_id: Optional[int] = None
    course_id: Optional[int] = None
    details: Optional[Dict[str, Any]] = None

@router.post("/log", status_code=status.HTTP_201_CREATED)
def record_activity(
    log: ActivityLogRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Log a specific user activity (e.g., viewing a material).
    """
    activity = models.ActivityLog(
        user_id=current_user.id,
        action=log.action,
        resource_type=log.resource_type,
        resource_id=log.resource_id,
        course_id=log.course_id,
        extra_data=log.details
    )
    db.add(activity)
    db.commit()
    return {"message": "Activity recorded"}
