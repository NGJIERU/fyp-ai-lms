"""
API endpoints for Student and Lecturer Dashboards
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from collections import defaultdict

from app import models
from app.api import deps
from app.core.database import get_db
from app.services.recommendation import get_recommendation_engine

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
    total_study_time_seconds: int = 0


class CourseDetailResponse(BaseModel):
    course_id: int
    course_name: str
    course_code: str
    lecturer_name: Optional[str]
    weekly_progress: List[WeeklyProgressItem]
    weak_topics: List[WeakTopicItem]
    overall_score: float
    total_attempts: int = 0  # Total quiz attempts (for UX: hide score if < 3)
    weeks_attempted: int = 0  # Weeks with any attempts (distinguished from completed)
    weeks_completed: int = 0  # Weeks with mastery >= 70%
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


class LecturerBundleMaterial(BaseModel):
    id: int
    title: str
    url: str
    source: str
    type: str


class LecturerBundleItem(BaseModel):
    course_id: int
    week_number: int
    topic: str
    summary: str
    materials: List[LecturerBundleMaterial]


class RatingInsightItem(BaseModel):
    material_id: int
    title: str
    course_id: int
    course_name: Optional[str]
    average_rating: float
    total_ratings: int
    upvotes: int
    downvotes: int


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
    students_count: int
    common_mistakes: List[str]


class LecturerDashboardResponse(BaseModel):
    lecturer_id: int
    lecturer_name: str
    courses: List[LecturerCourseStats]
    total_students: int
    pending_material_approvals: int
    recent_submissions: List[Dict[str, Any]]
    context_bundles: List[LecturerBundleItem] = []
    rating_insights: List[RatingInsightItem] = []


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
    
    # Get recent activity (Fetch more to allow for grouping group)
    raw_activity = (
        db.query(models.ActivityLog)
        .filter(models.ActivityLog.user_id == current_user.id)
        .order_by(desc(models.ActivityLog.created_at))
        .limit(50) 
        .all()
    )
    
    # Group consecutive quiz attempts
    activity_list = []
    if raw_activity:
        # We iterate through the raw list. Since it's ordered by DESC (newest first),
        # we can group "older" identical actions into the "newer" one.
        
        current_group = None
        
        for log in raw_activity:
            is_quiz = (log.action == "submit_quiz_attempt")
            
            # Start a new group if:
            # 1. No current group
            # 2. Action is different
            # 3. Time gap is too large (> 5 mins)
            if current_group:
                time_diff = (current_group["_raw_time"] - log.created_at).total_seconds()
                same_action = (current_group["action"] == log.action)
                
                if same_action and is_quiz and time_diff < 300: # 5 minutes grouping window
                    # Merge into current group
                    current_group["count"] = current_group.get("count", 1) + 1
                    continue
                else:
                    # Finalize current group and start new one
                    # Format the action label for the finished group
                    if current_group.get("count", 1) > 1:
                        current_group["action"] = f"Completed {current_group['count']} practice questions"
                    
                    # Remove internal helper keys
                    raw_time = current_group.pop("_raw_time")
                    count = current_group.pop("count", None)
                    
                    activity_list.append(current_group)
                    current_group = None

            # Create new group item
            current_group = {
                "action": log.action,
                "resource_type": log.resource_type,
                "created_at": log.created_at.isoformat(),
                "_raw_time": log.created_at,
                "count": 1
            }
        
        # Append the last trailing group
        if current_group:
            if current_group.get("count", 1) > 1:
                current_group["action"] = f"Completed {current_group['count']} practice questions"
            current_group.pop("_raw_time")
            current_group.pop("count", None)
            activity_list.append(current_group)

    # Limit to top 10 after grouping
    activity_list = activity_list[:10]
    
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
        total_study_time_hours=round(total_hours, 1),
        total_study_time_seconds=int(sessions or 0)
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
            
            # NORMALIZATION: Convert 0-100 store to 0-1 ratio for frontend
            raw_score = performance.average_score
            score = raw_score / 100.0 if raw_score > 1.0 else raw_score
            
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
                    average_score=score, # Normalized
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
    
    # Count materials accessed (distinct materials viewed in this course)
    # Count materials accessed (distinct materials viewed in this course AND in syllabus)
    materials_accessed = (
        db.query(models.ActivityLog.resource_id)
        .join(models.MaterialTopic, 
              (models.MaterialTopic.material_id == models.ActivityLog.resource_id) & 
              (models.MaterialTopic.course_id == course_id) &
              (models.MaterialTopic.approved_by_lecturer == True)
        )
        .filter(
            models.ActivityLog.user_id == current_user.id,
            models.ActivityLog.action == "view_material",
            models.ActivityLog.resource_type == "material",
            models.ActivityLog.course_id == course_id
        )
        .distinct()
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
    
    # Calculate overall score as percentage (0-100)
    overall_score = ((total_score / scored_weeks) * 100) if scored_weeks > 0 else 0
    
    # Calculate aggregate stats for UX
    total_attempts = (
        db.query(func.sum(models.TopicPerformance.total_attempts))
        .filter(
            models.TopicPerformance.student_id == current_user.id,
            models.TopicPerformance.course_id == course_id
        )
        .scalar() or 0
    )
    
    weeks_completed = (
        db.query(models.TopicPerformance)
        .filter(
            models.TopicPerformance.student_id == current_user.id,
            models.TopicPerformance.course_id == course_id,
            models.TopicPerformance.mastery_level.in_(["proficient", "mastered"])
        )
        .count()
    )
    
    return CourseDetailResponse(
        course_id=course.id,
        course_name=course.name,
        course_code=course.code,
        lecturer_name=lecturer_name,
        weekly_progress=weekly_progress,
        weak_topics=weak_topics,
        overall_score=round(overall_score, 1),
        total_attempts=int(total_attempts),
        weeks_attempted=scored_weeks,  # scored_weeks = weeks with any performance data
        weeks_completed=weeks_completed,
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
    
    course_stats: List[LecturerCourseStats] = []
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
        
        if avg_score_result is None:
            avg_score = 0.0
        else:
            raw_val = float(avg_score_result)
            if raw_val > 1.0:
                 final_percent = raw_val
            else:
                 final_percent = raw_val * 100.0
            
            avg_score = min(max(final_percent, 0.0), 100.0)
        
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
    
    recent_sessions = (
        db.query(
            models.QuizAttempt.student_id,
            models.QuizAttempt.course_id,
            models.QuizAttempt.week_number,
            func.sum(models.QuizAttempt.score).label("total_score"),
            func.sum(models.QuizAttempt.max_score).label("total_max_score"),
            func.count(models.QuizAttempt.id).label("questions_count"),
            func.max(models.QuizAttempt.attempted_at).label("last_attempted_at"),
        )
        .join(models.Course, models.QuizAttempt.course_id == models.Course.id)
        .filter(models.Course.lecturer_id == current_user.id)
        .group_by(
            models.QuizAttempt.student_id,
            models.QuizAttempt.course_id,
            models.QuizAttempt.week_number,
            func.date(models.QuizAttempt.attempted_at),
        )
        .order_by(desc(func.max(models.QuizAttempt.attempted_at)))
        .limit(10)
        .all()
    )
    
    submissions_list = [
        {
            "student_id": s.student_id,
            "course_id": s.course_id,
            "week_number": s.week_number,
            "score": (s.total_score / s.total_max_score * 100) if s.total_max_score > 0 else 0,
            "questions_answered": s.questions_count,
            "attempted_at": s.last_attempted_at.isoformat() if s.last_attempted_at else None
        }
        for s in recent_sessions
    ]

    # Context bundles per course (limited for dashboard view)
    engine = get_recommendation_engine()
    context_bundles: List[LecturerBundleItem] = []
    for course in courses:
        bundles = engine.generate_context_bundles(
            db=db,
            course_id=course.id,
            max_bundles=2,
            materials_per_bundle=3,
            include_scores=False,
        )
        for bundle in bundles:
            materials = [
                LecturerBundleMaterial(
                    id=m["id"],
                    title=m["title"],
                    url=m["url"],
                    source=m["source"],
                    type=m["type"],
                )
                for m in bundle.get("materials", [])
            ]
            context_bundles.append(
                LecturerBundleItem(
                    course_id=bundle["course_id"],
                    week_number=bundle["week_number"],
                    topic=bundle["topic"],
                    summary=bundle["summary"],
                    materials=materials,
                )
            )

    # Rating insights: identify lowest-rated materials across lecturer's courses
    rating_insights: List[RatingInsightItem] = []
    ratings = (
        db.query(models.MaterialRating)
        .join(models.Material, models.MaterialRating.material_id == models.Material.id)
        .outerjoin(
            models.MaterialTopic,
            models.MaterialTopic.material_id == models.Material.id,
        )
        .outerjoin(
            models.Course,
            models.MaterialTopic.course_id == models.Course.id,
        )
        .filter(models.Course.lecturer_id == current_user.id)
        .all()
    )

    grouped: Dict[int, Dict[str, Any]] = defaultdict(
        lambda: {"ratings": [], "material": None, "course": None}
    )
    for r in ratings:
        mat = r.material
        # Find any associated course via topics owned by this lecturer
        topic = None
        for t in mat.topics:
            if t.course.lecturer_id == current_user.id:
                topic = t
                break
        course = topic.course if topic else None
        entry = grouped[mat.id]
        entry["ratings"].append(r.rating)
        entry["material"] = mat
        entry["course"] = course

    MIN_RATINGS = 3
    for material_id, info in grouped.items():
        vals = info["ratings"]
        if len(vals) < MIN_RATINGS:
            continue
        mat = info["material"]
        course = info["course"]
        avg = sum(vals) / len(vals)
        upvotes = sum(1 for v in vals if v == 1)
        downvotes = sum(1 for v in vals if v == -1)
        rating_insights.append(
            RatingInsightItem(
                material_id=material_id,
                title=mat.title,
                course_id=course.id if course else 0,
                course_name=course.name if course else None,
                average_rating=avg,
                total_ratings=len(vals),
                upvotes=upvotes,
                downvotes=downvotes,
            )
        )

    # Sort to show worst-rated first and limit list
    rating_insights.sort(key=lambda r: r.average_rating)
    rating_insights = rating_insights[:10]

    return LecturerDashboardResponse(
        lecturer_id=current_user.id,
        lecturer_name=current_user.full_name or current_user.email,
        courses=course_stats,
        total_students=total_students,
        pending_material_approvals=total_pending,
        recent_submissions=submissions_list,
        context_bundles=context_bundles,
        rating_insights=rating_insights,
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
        
        if avg_score_result is None:
            avg_score = 0.0
        else:
            raw_val = float(avg_score_result)
            if raw_val > 1.0:
                final_percent = raw_val
            else:
                 final_percent = raw_val * 100.0
            
            avg_score = min(max(final_percent, 0.0), 100.0)
        
        weak_topics_query = (
            db.query(models.Syllabus.topic)
            .join(models.TopicPerformance, 
                  (models.TopicPerformance.course_id == models.Syllabus.course_id) & 
                  (models.TopicPerformance.week_number == models.Syllabus.week_number))
            .filter(
                models.TopicPerformance.student_id == student.id,
                models.TopicPerformance.course_id == course_id,
                models.Syllabus.is_active == True,
                models.TopicPerformance.total_attempts > 0
            )
            .order_by(models.TopicPerformance.average_score.asc())
            .limit(2)
            .all()
        )
        
        weak_topic_names = [w[0] for w in weak_topics_query]
        
        last_active_time = None
        
        last_log = (
            db.query(models.ActivityLog)
            .filter(models.ActivityLog.user_id == student.id)
            .order_by(desc(models.ActivityLog.created_at))
            .first()
        )
        if last_log:
            last_active_time = last_log.created_at

        # If no activity log, check for recent quiz attempts
        if not last_active_time:
            last_quiz = (
                db.query(models.QuizAttempt)
                .join(models.Course, models.QuizAttempt.course_id == models.Course.id)
                .filter(models.QuizAttempt.student_id == student.id)
                .order_by(desc(models.QuizAttempt.attempted_at))
                .first()
            )
            if last_quiz:
                last_active_time = last_quiz.attempted_at
        
        # If still no activity, check topic performance updates
        if not last_active_time:
            last_perf = (
                db.query(models.TopicPerformance)
                .filter(models.TopicPerformance.student_id == student.id)
                .order_by(desc(models.TopicPerformance.last_attempt_at))
                .first()
            )
            if last_perf:
                last_active_time = last_perf.last_attempt_at
        
        students_performance.append(StudentPerformanceItem(
            student_id=student.id,
            student_name=student.full_name or student.email,
            email=student.email,
            average_score=round(avg_score, 1),
            weak_topics=weak_topic_names,
            last_active=last_active_time
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
                func.sum(models.TopicPerformance.total_attempts).label('total_attempts'),
                func.count(models.TopicPerformance.student_id).label('students_count')
            )
            .filter(
                models.TopicPerformance.course_id == course_id,
                models.TopicPerformance.week_number == entry.week_number
            )
            .first()
        )
        
        # average_score is already stored as 0-100 percentage in database
        # (see ai_tutor.py line 396: current_score_pct = ... * 100)
        avg_score = stats.avg_score or 0
        attempts = stats.total_attempts or 0
        students = stats.students_count or 0
        
        # Common mistakes would come from analyzing quiz attempts
        # For now, return placeholder
        common_mistakes = []
        
        analytics.append(WeekAnalytics(
            week_number=entry.week_number,
            topic=entry.topic,
            avg_score=round(avg_score, 1),
            attempts_count=attempts,
            students_count=students,
            common_mistakes=common_mistakes
        ))
    
    return analytics
