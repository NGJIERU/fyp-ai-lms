from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app import models, schemas
from app.api import deps
from app.core.database import get_db

router = APIRouter()

@router.post("/", response_model=schemas.course.CourseRead, status_code=status.HTTP_201_CREATED)
def create_course(
    course_in: schemas.course.CourseCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_lecturer),
):
    """
    Create a new course. Only lecturers and super admins can create courses.
    """
    # Check if course code already exists
    existing_course = db.query(models.Course).filter(models.Course.code == course_in.code).first()
    if existing_course:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Course with code '{course_in.code}' already exists"
        )
    
    # Verify lecturer exists (if provided)
    if course_in.lecturer_id:
        lecturer = db.query(models.User).filter(
            models.User.id == course_in.lecturer_id,
            models.User.role.in_([models.UserRole.LECTURER, models.UserRole.SUPER_ADMIN])
        ).first()
        if not lecturer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lecturer with ID {course_in.lecturer_id} not found or is not a lecturer"
            )
    
    # Create course
    db_course = models.Course(**course_in.dict())
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    
    # Load lecturer relationship for response
    db.refresh(db_course, ['lecturer'])
    
    # Create response with lecturer_name
    course_dict = {
        **db_course.__dict__,
        'lecturer_name': db_course.lecturer.full_name if db_course.lecturer else None
    }
    return schemas.course.CourseRead(**course_dict)

@router.get("/", response_model=List[schemas.course.CourseRead])
def list_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    lecturer_id: Optional[int] = Query(None, description="Filter by lecturer ID"),
    search: Optional[str] = Query(None, description="Search by course name or code"),
    db: Session = Depends(get_db),
):
    """
    List all courses with optional filtering and pagination.
    Public endpoint - all authenticated users can view courses.
    """
    query = db.query(models.Course)
    
    # Filter by lecturer
    if lecturer_id:
        query = query.filter(models.Course.lecturer_id == lecturer_id)
    
    # Search by name or code
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (models.Course.name.ilike(search_term)) |
            (models.Course.code.ilike(search_term))
        )
    
    courses = query.offset(skip).limit(limit).all()
    
    # Load lecturer relationships and create response
    result = []
    for course in courses:
        db.refresh(course, ['lecturer'])
        course_dict = {
            **course.__dict__,
            'lecturer_name': course.lecturer.full_name if course.lecturer else None
        }
        result.append(schemas.course.CourseRead(**course_dict))
    
    return result

@router.get("/{course_id}", response_model=schemas.course.CourseRead)
def get_course(
    course_id: int,
    db: Session = Depends(get_db),
):
    """
    Get a specific course by ID.
    Public endpoint - all authenticated users can view course details.
    """
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Load lecturer relationship
    db.refresh(course, ['lecturer'])
    
    # Create response with lecturer_name
    course_dict = {
        **course.__dict__,
        'lecturer_name': course.lecturer.full_name if course.lecturer else None
    }
    return schemas.course.CourseRead(**course_dict)

@router.put("/{course_id}", response_model=schemas.course.CourseRead)
def update_course(
    course_id: int,
    course_in: schemas.course.CourseUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_lecturer),
):
    """
    Update a course. Only lecturers and super admins can update courses.
    Lecturers can only update their own courses unless they are super admin.
    """
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check authorization: Lecturers can only update their own courses
    if current_user.role == models.UserRole.LECTURER and course.lecturer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update courses assigned to you"
        )
    
    # Verify lecturer exists if updating lecturer_id
    if course_in.lecturer_id is not None:
        lecturer = db.query(models.User).filter(
            models.User.id == course_in.lecturer_id,
            models.User.role.in_([models.UserRole.LECTURER, models.UserRole.SUPER_ADMIN])
        ).first()
        if not lecturer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lecturer with ID {course_in.lecturer_id} not found or is not a lecturer"
            )
    
    # Update fields
    update_data = course_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(course, field, value)
    
    db.commit()
    db.refresh(course)
    
    # Load lecturer relationship
    db.refresh(course, ['lecturer'])
    
    # Create response with lecturer_name
    course_dict = {
        **course.__dict__,
        'lecturer_name': course.lecturer.full_name if course.lecturer else None
    }
    return schemas.course.CourseRead(**course_dict)

@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Delete a course. Only super admins can delete courses.
    This will cascade delete all associated syllabus entries.
    """
    # Check if user is super admin
    if current_user.role != models.UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admins can delete courses"
        )
    
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    db.delete(course)
    db.commit()
    return None


@router.post("/{course_id}/students", response_model=schemas.course.CourseStudentResponse, status_code=status.HTTP_201_CREATED)
def enroll_student_by_email(
    course_id: int,
    enroll_in: schemas.course.CourseStudentEnroll,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_lecturer),
):
    """
    Enroll a student into a course by email.
    Only the course lecturer or super admin can perform this action.
    """
    # Verify course exists
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Access control: Lecturer must own the course
    if current_user.role == models.UserRole.LECTURER and course.lecturer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only manage students for your own courses"
        )

    # Find the student
    student = db.query(models.User).filter(
        models.User.email == enroll_in.email,
        # Potentially verify role is STUDENT. But maybe we allow enrolling anyone?
        # Usually only students should be enrolled as students.
        # Let's enforce role=STUDENT for clarity.
        models.User.role == models.UserRole.STUDENT
    ).first()

    if not student:
        raise HTTPException(status_code=404, detail=f"No student account found with email {enroll_in.email}")

    # Check existing enrollment
    existing = (
        db.query(models.StudentEnrollment)
        .filter(
            models.StudentEnrollment.student_id == student.id,
            models.StudentEnrollment.course_id == course_id
        )
        .first()
    )

    if existing:
        if existing.is_active:
            raise HTTPException(status_code=409, detail="Student is already enrolled in this course")
        else:
            # Reactivate
            existing.is_active = True
            db.commit()
            return {
                "student_id": student.id,
                "course_id": course_id,
                "message": "Student re-enrolled successfully",
                "student_name": student.full_name or student.email,
                "student_email": student.email
            }

    # Create new enrollment
    enrollment = models.StudentEnrollment(
        student_id=student.id,
        course_id=course_id
    )
    db.add(enrollment)
    db.commit()

    return {
        "student_id": student.id,
        "course_id": course_id,
        "message": "Student enrolled successfully",
        "student_name": student.full_name or student.email,
        "student_email": student.email
    }


@router.delete("/{course_id}/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_student_from_course(
    course_id: int,
    student_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_lecturer),
):
    """
    Remove (un-enroll) a student from a course.
    """
    # Verify course exists
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Access control
    if current_user.role == models.UserRole.LECTURER and course.lecturer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only manage students for your own courses"
        )

    # Find enrollment
    enrollment = (
        db.query(models.StudentEnrollment)
        .filter(
            models.StudentEnrollment.student_id == student_id,
            models.StudentEnrollment.course_id == course_id
        )
        .first()
    )

    if not enrollment:
        raise HTTPException(status_code=404, detail="Student is not enrolled in this course")

    # Hard delete or soft delete?
    # Let's do hard delete to keep it simple and clean, OR soft delete (is_active=False).
    # The models for analytics often rely on enrollment existence. 
    # For now, let's just DELETE the record to fully remove them.
    # But wait, foreign keys on quiz attempts might cascade or break.
    # The QuizAttempt model has ondelete="CASCADE", so deleting user deletes attempts.
    # Actually, StudentEnrollment doesn't seem to be parent of QuizAttempt directly.
    # Let's check StudentEnrollment definition again. It doesn't have cascades from it.
    # So deleting enrollment is safe.
    
    db.delete(enrollment)
    db.commit()
    return None
