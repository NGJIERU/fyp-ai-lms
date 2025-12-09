"""
API endpoints for Student and Lecturer Dashboards
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

from app import models
from app.api import deps
from app.core.database import get_db

router = APIRouter()


# ==================== Pydantic Schemas ====================

class EnrolledCourseItem(BaseModel):
    course_id: int
    code: str
    name: str
    lecturer_name: Optional[str]
    progress_percent: float = 0.0
    weak_topics_count: int = 0

    class Config:
        from_attributes = True


class WeeklyProgressItem(BaseModel):
    week_number: int
    topic: str
    status: str  # not_started, in_progress, completed
    score: Optional[float]
    materials_count: int


class MaterialItem(BaseModel):
    id: int
    title: str
    url: str
    source: str
    type: str
    quality_score: float


class WeakTopicItem(BaseModel):
    week_number: int
    topic: str
    average_score: float
    attempts: int
    recommended_materials: List[MaterialItem] = []


class StudentDashboardResponse(BaseModel):
    student_id: int
    student_name: str
    enrolled_courses: List[EnrolledCourseItem]
    recent_activity: List[Dict[str, Any]]
    weak_topics_summary: Dict[str, int]  # course_id -> count
    total_study_time_hours: float


class CourseDetailResponse(BaseModel):
    course_id: int
    course_name: str
    course_code: str
    lecturer_name: Optional[str]
    weekly_progress: List[WeeklyProgressItem]
    weak_topics: List[WeakTopicItem]
    overall_score: float
    materials_accessed: int
    total_materials: int


class LecturerCourseStats(BaseModel):
    course_id: int
    course_code: str
    course_name: str
    enrolled_students: int
    avg_class_score: float
    materials_count: int
    pending_approvals: int


class StudentPerformanceItem(BaseModel):
    student_id: int
    student_name: str
    email: str
    average_score: float
    weak_topics: List[str]
    last_active: Optional[datetime]


class WeekAnalytics(BaseModel):
    week_number: int
    topic: str
    avg_score: float
    attempts_count: int
    common_mistakes: List[str]


class LecturerDashboardResponse(BaseModel):
    lecturer_id: int
    lecturer_name: str
    courses: List[LecturerCourseStats]
    total_students: int
    pending_material_approvals: int
    recent_submissions: List[Dict[str, Any]]


# ==================== Student Dashboard Endpoints ====================

@router.get("/student", response_model=StudentDashboardResponse)
def get_student_dashboard(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Get the student dashboard overview.
    Shows enrolled courses, progress, and weak topics summary.
    """
    if current_user.role not in [models.UserRole.STUDENT, models.UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can access this dashboard"
        )
    
    # Get enrolled courses
    enrollments = (
        db.query(models.StudentEnrollment)
        .filter(
            models.StudentEnrollment.student_id == current_user.id,
            models.StudentEnrollment.is_active == True
        )
        .all()
    )
    
    enrolled_courses = []
    weak_topics_summary = {}
    
    for enrollment in enrollments:
        course = db.query(models.Course).filter(models.Course.id == enrollment.course_id).first()
        if not course:
            continue
        
        # Get weak topics count
        weak_count = (
            db.query(models.TopicPerformance)
            .filter(
                models.TopicPerformance.student_id == current_user.id,
                models.TopicPerformance.course_id == course.id,
                models.TopicPerformance.is_weak_topic == True
            )
            .count()
        )
        
        # Calculate progress
        total_weeks = (
            db.query(models.Syllabus)
            .filter(
                models.Syllabus.course_id == course.id,
                models.Syllabus.is_active == True
            )
            .count()
        )
        
        completed_weeks = (
            db.query(models.TopicPerformance)
            .filter(
                models.TopicPerformance.student_id == current_user.id,
                models.TopicPerformance.course_id == course.id,
                models.TopicPerformance.mastery_level.in_(["proficient", "mastered"])
            )
            .count()
        )
        
        progress = (completed_weeks / total_weeks * 100) if total_weeks > 0 else 0
        
        lecturer_name = None
        if course.lecturer_id:
            lecturer = db.query(models.User).filter(models.User.id == course.lecturer_id).first()
            lecturer_name = lecturer.full_name if lecturer else None
        
        enrolled_courses.append(EnrolledCourseItem(
            course_id=course.id,
            code=course.code,
            name=course.name,
            lecturer_name=lecturer_name,
            progress_percent=progress,
            weak_topics_count=weak_count
        ))
        
        weak_topics_summary[str(course.id)] = weak_count
    
    # Get recent activity
    recent_activity = (
        db.query(models.ActivityLog)
        .filter(models.ActivityLog.user_id == current_user.id)
        .order_by(desc(models.ActivityLog.created_at))
        .limit(10)
        .all()
    )
    
    activity_list = [
        {
            "action": a.action,
            "resource_type": a.resource_type,
            "created_at": a.created_at.isoformat() if a.created_at else None
        }
        for a in recent_activity
    ]
    
    # Calculate total study time
    sessions = (
        db.query(func.sum(models.LearningSession.duration_seconds))
        .filter(models.LearningSession.student_id == current_user.id)
        .scalar()
    )
    total_hours = (sessions or 0) / 3600
    
    return StudentDashboardResponse(
        student_id=current_user.id,
        student_name=current_user.full_name or current_user.email,
        enrolled_courses=enrolled_courses,
        recent_activity=activity_list,
        weak_topics_summary=weak_topics_summary,
        total_study_time_hours=round(total_hours, 1)
    )


@router.get("/student/course/{course_id}", response_model=CourseDetailResponse)
def get_student_course_detail(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Get detailed course view for a student.
    Shows weekly progress, materials, and weak topics.
    """
    # Verify enrollment
    enrollment = (
        db.query(models.StudentEnrollment)
        .filter(
            models.StudentEnrollment.student_id == current_user.id,
            models.StudentEnrollment.course_id == course_id,
            models.StudentEnrollment.is_active == True
        )
        .first()
    )
    
    # Allow access for admins even without enrollment
    if not enrollment and current_user.role != models.UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not enrolled in this course"
        )
    
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Get syllabus entries
    syllabus_entries = (
        db.query(models.Syllabus)
        .filter(
            models.Syllabus.course_id == course_id,
            models.Syllabus.is_active == True
        )
        .order_by(models.Syllabus.week_number)
        .all()
    )
    
    weekly_progress = []
    weak_topics = []
    total_score = 0
    scored_weeks = 0
    
    for entry in syllabus_entries:
        # Get performance for this week
        performance = (
            db.query(models.TopicPerformance)
            .filter(
                models.TopicPerformance.student_id == current_user.id,
                models.TopicPerformance.course_id == course_id,
                models.TopicPerformance.week_number == entry.week_number
            )
            .first()
        )
        
        # Get materials count for this week
        materials_count = (
            db.query(models.MaterialTopic)
            .filter(
                models.MaterialTopic.course_id == course_id,
                models.MaterialTopic.week_number == entry.week_number,
                models.MaterialTopic.approved_by_lecturer == True
            )
            .count()
        )
        
        if performance:
            status_str = performance.mastery_level
            score = performance.average_score
            total_score += score
            scored_weeks += 1
            
            if performance.is_weak_topic:
                # Get recommended materials
                recommended = (
                    db.query(models.Material)
                    .join(models.MaterialTopic)
                    .filter(
                        models.MaterialTopic.course_id == course_id,
                        models.MaterialTopic.week_number == entry.week_number,
                        models.MaterialTopic.approved_by_lecturer == True
                    )
                    .limit(3)
                    .all()
                )
                
                weak_topics.append(WeakTopicItem(
                    week_number=entry.week_number,
                    topic=entry.topic,
                    average_score=score,
                    attempts=performance.total_attempts,
                    recommended_materials=[
                        MaterialItem(
                            id=m.id,
                            title=m.title,
                            url=m.url,
                            source=m.source,
                            type=m.type,
                            quality_score=m.quality_score
                        )
                        for m in recommended
                    ]
                ))
        else:
            status_str = "not_started"
            score = None
        
        weekly_progress.append(WeeklyProgressItem(
            week_number=entry.week_number,
            topic=entry.topic,
            status=status_str,
            score=score,
            materials_count=materials_count
        ))
    
    # Get lecturer name
    lecturer_name = None
    if course.lecturer_id:
        lecturer = db.query(models.User).filter(models.User.id == course.lecturer_id).first()
        lecturer_name = lecturer.full_name if lecturer else None
    
    # Count materials accessed
    materials_accessed = (
        db.query(models.ActivityLog)
        .filter(
            models.ActivityLog.user_id == current_user.id,
            models.ActivityLog.action == "view_material",
            models.ActivityLog.resource_type == "material"
        )
        .count()
    )
    
    total_materials = (
        db.query(models.MaterialTopic)
        .filter(
            models.MaterialTopic.course_id == course_id,
            models.MaterialTopic.approved_by_lecturer == True
        )
        .count()
    )
    
    overall_score = (total_score / scored_weeks * 100) if scored_weeks > 0 else 0
    
    return CourseDetailResponse(
        course_id=course.id,
        course_name=course.name,
        course_code=course.code,
        lecturer_name=lecturer_name,
        weekly_progress=weekly_progress,
        weak_topics=weak_topics,
        overall_score=round(overall_score, 1),
        materials_accessed=materials_accessed,
        total_materials=total_materials
    )


@router.post("/student/enroll/{course_id}")
def enroll_in_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Enroll the current student in a course.
    """
    if current_user.role not in [models.UserRole.STUDENT, models.UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can enroll in courses"
        )
    
    # Check course exists
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check if already enrolled
    existing = (
        db.query(models.StudentEnrollment)
        .filter(
            models.StudentEnrollment.student_id == current_user.id,
            models.StudentEnrollment.course_id == course_id
        )
        .first()
    )
    
    if existing:
        if existing.is_active:
            raise HTTPException(status_code=400, detail="Already enrolled in this course")
        else:
            # Reactivate enrollment
            existing.is_active = True
            db.commit()
            return {"message": "Re-enrolled in course successfully"}
    
    # Create enrollment
    enrollment = models.StudentEnrollment(
        student_id=current_user.id,
        course_id=course_id
    )
    db.add(enrollment)
    db.commit()
    
    return {"message": "Enrolled in course successfully", "course_id": course_id}


# ==================== Lecturer Dashboard Endpoints ====================

@router.get("/lecturer", response_model=LecturerDashboardResponse)
def get_lecturer_dashboard(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_lecturer),
):
    """
    Get the lecturer dashboard overview.
    Shows courses, student stats, and pending approvals.
    """
    # Get lecturer's courses
    courses = (
        db.query(models.Course)
        .filter(models.Course.lecturer_id == current_user.id)
        .all()
    )
    
    course_stats = []
    total_students = 0
    total_pending = 0
    
    for course in courses:
        # Count enrolled students
        enrolled = (
            db.query(models.StudentEnrollment)
            .filter(
                models.StudentEnrollment.course_id == course.id,
                models.StudentEnrollment.is_active == True
            )
            .count()
        )
        total_students += enrolled
        
        # Calculate average class score
        avg_score_result = (
            db.query(func.avg(models.TopicPerformance.average_score))
            .filter(models.TopicPerformance.course_id == course.id)
            .scalar()
        )
        avg_score = (avg_score_result or 0) * 100
        
        # Count materials
        materials_count = (
            db.query(models.MaterialTopic)
            .filter(
                models.MaterialTopic.course_id == course.id,
                models.MaterialTopic.approved_by_lecturer == True
            )
            .count()
        )
        
        # Count pending approvals
        pending = (
            db.query(models.MaterialTopic)
            .filter(
                models.MaterialTopic.course_id == course.id,
                models.MaterialTopic.approved_by_lecturer == False
            )
            .count()
        )
        total_pending += pending
        
        course_stats.append(LecturerCourseStats(
            course_id=course.id,
            course_code=course.code,
            course_name=course.name,
            enrolled_students=enrolled,
            avg_class_score=round(avg_score, 1),
            materials_count=materials_count,
            pending_approvals=pending
        ))
    
    # Get recent submissions
    recent_submissions = (
        db.query(models.QuizAttempt)
        .join(models.Course, models.QuizAttempt.course_id == models.Course.id)
        .filter(models.Course.lecturer_id == current_user.id)
        .order_by(desc(models.QuizAttempt.attempted_at))
        .limit(10)
        .all()
    )
    
    submissions_list = [
        {
            "student_id": s.student_id,
            "course_id": s.course_id,
            "week_number": s.week_number,
            "score": s.score,
            "attempted_at": s.attempted_at.isoformat() if s.attempted_at else None
        }
        for s in recent_submissions
    ]
    
    return LecturerDashboardResponse(
        lecturer_id=current_user.id,
        lecturer_name=current_user.full_name or current_user.email,
        courses=course_stats,
        total_students=total_students,
        pending_material_approvals=total_pending,
        recent_submissions=submissions_list
    )


@router.get("/lecturer/course/{course_id}/students", response_model=List[StudentPerformanceItem])
def get_course_students_performance(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_lecturer),
):
    """
    Get performance data for all students in a course.
    """
    # Verify course ownership
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if current_user.role == models.UserRole.LECTURER and course.lecturer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view students for your own courses"
        )
    
    # Get enrolled students
    enrollments = (
        db.query(models.StudentEnrollment)
        .filter(
            models.StudentEnrollment.course_id == course_id,
            models.StudentEnrollment.is_active == True
        )
        .all()
    )
    
    students_performance = []
    
    for enrollment in enrollments:
        student = db.query(models.User).filter(models.User.id == enrollment.student_id).first()
        if not student:
            continue
        
        # Get average score
        avg_score_result = (
            db.query(func.avg(models.TopicPerformance.average_score))
            .filter(
                models.TopicPerformance.student_id == student.id,
                models.TopicPerformance.course_id == course_id
            )
            .scalar()
        )
        avg_score = (avg_score_result or 0) * 100
        
        # Get weak topics
        weak_topics = (
            db.query(models.TopicPerformance)
            .join(models.Syllabus, 
                  (models.TopicPerformance.course_id == models.Syllabus.course_id) & 
                  (models.TopicPerformance.week_number == models.Syllabus.week_number))
            .filter(
                models.TopicPerformance.student_id == student.id,
                models.TopicPerformance.course_id == course_id,
                models.TopicPerformance.is_weak_topic == True,
                models.Syllabus.is_active == True
            )
            .all()
        )
        
        weak_topic_names = []
        for wt in weak_topics:
            syllabus = (
                db.query(models.Syllabus)
                .filter(
                    models.Syllabus.course_id == course_id,
                    models.Syllabus.week_number == wt.week_number,
                    models.Syllabus.is_active == True
                )
                .first()
            )
            if syllabus:
                weak_topic_names.append(syllabus.topic)
        
        # Get last activity
        last_activity = (
            db.query(models.ActivityLog)
            .filter(models.ActivityLog.user_id == student.id)
            .order_by(desc(models.ActivityLog.created_at))
            .first()
        )
        
        students_performance.append(StudentPerformanceItem(
            student_id=student.id,
            student_name=student.full_name or student.email,
            email=student.email,
            average_score=round(avg_score, 1),
            weak_topics=weak_topic_names,
            last_active=last_activity.created_at if last_activity else None
        ))
    
    return students_performance


@router.get("/lecturer/course/{course_id}/analytics", response_model=List[WeekAnalytics])
def get_course_week_analytics(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_lecturer),
):
    """
    Get analytics for each week of a course.
    Shows average scores and common problem areas.
    """
    # Verify course ownership
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if current_user.role == models.UserRole.LECTURER and course.lecturer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view analytics for your own courses"
        )
    
    # Get syllabus entries
    syllabus_entries = (
        db.query(models.Syllabus)
        .filter(
            models.Syllabus.course_id == course_id,
            models.Syllabus.is_active == True
        )
        .order_by(models.Syllabus.week_number)
        .all()
    )
    
    analytics = []
    
    for entry in syllabus_entries:
        # Get aggregated stats for this week
        stats = (
            db.query(
                func.avg(models.TopicPerformance.average_score).label('avg_score'),
                func.sum(models.TopicPerformance.total_attempts).label('total_attempts')
            )
            .filter(
                models.TopicPerformance.course_id == course_id,
                models.TopicPerformance.week_number == entry.week_number
            )
            .first()
        )
        
        avg_score = (stats.avg_score or 0) * 100
        attempts = stats.total_attempts or 0
        
        # Common mistakes would come from analyzing quiz attempts
        # For now, return placeholder
        common_mistakes = []
        
        analytics.append(WeekAnalytics(
            week_number=entry.week_number,
            topic=entry.topic,
            avg_score=round(avg_score, 1),
            attempts_count=attempts,
            common_mistakes=common_mistakes
        ))
    
    return analytics
