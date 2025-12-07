from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app import models, schemas
from app.api import deps
from app.core.database import get_db

router = APIRouter()

def format_syllabus_response(syllabus_entry: models.Syllabus) -> schemas.syllabus.SyllabusRead:
    """Helper function to format syllabus response with relationships"""
    syllabus_dict = {
        **syllabus_entry.__dict__,
        'created_by_name': syllabus_entry.creator.full_name if syllabus_entry.creator else None,
        'course_name': syllabus_entry.course.name if syllabus_entry.course else None
    }
    return schemas.syllabus.SyllabusRead(**syllabus_dict)

@router.get("/", response_model=List[schemas.syllabus.SyllabusRead])
def list_syllabus(
    course_id: int = Query(..., description="ID of the course"),
    include_inactive: bool = Query(False, description="Include inactive syllabus entries (lecturers/admin only)"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    List syllabus entries for a course.
    Students see only active entries. Lecturers and admins can see all entries.
    """
    # Verify course exists
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    query = db.query(models.Syllabus).filter(models.Syllabus.course_id == course_id)
    
    # Students only see active entries
    if current_user.role == models.UserRole.STUDENT or not include_inactive:
        query = query.filter(models.Syllabus.is_active == True)
    
    syllabus_entries = query.order_by(models.Syllabus.week_number).all()
    
    # Load relationships and format response
    result = []
    for entry in syllabus_entries:
        db.refresh(entry, ['course', 'creator'])
        result.append(format_syllabus_response(entry))
    
    return result

@router.post("/", response_model=schemas.syllabus.SyllabusRead, status_code=status.HTTP_201_CREATED)
def create_syllabus(
    syllabus_in: schemas.syllabus.SyllabusCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_lecturer),
):
    """
    Create a new syllabus entry for a specific week.
    Only lecturers and super admins can create syllabus entries.
    """
    # Ensure course exists
    course = db.query(models.Course).filter(models.Course.id == syllabus_in.course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check authorization: Lecturers can only create syllabus for their own courses
    if current_user.role == models.UserRole.LECTURER and course.lecturer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create syllabus for courses assigned to you"
        )
    
    # Check if active record exists for (course_id, week_number)
    existing_active = (
        db.query(models.Syllabus)
        .filter(
            models.Syllabus.course_id == syllabus_in.course_id,
            models.Syllabus.week_number == syllabus_in.week_number,
            models.Syllabus.is_active == True
        )
        .first()
    )
    if existing_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Active syllabus already exists for week {syllabus_in.week_number}. Use PUT to update."
        )
    
    # Create new syllabus entry (version starts at 1)
    db_syllabus = models.Syllabus(
        **syllabus_in.dict(exclude={'change_reason'}),
        version=1,
        is_active=True,
        created_by=current_user.id,
        change_reason=syllabus_in.change_reason or "Initial creation"
    )
    db.add(db_syllabus)
    db.commit()
    db.refresh(db_syllabus)
    
    # Load relationships
    db.refresh(db_syllabus, ['course', 'creator'])
    
    return format_syllabus_response(db_syllabus)

@router.post("/bulk", response_model=List[schemas.syllabus.SyllabusRead], status_code=status.HTTP_201_CREATED)
def create_syllabus_bulk(
    bulk_in: schemas.syllabus.SyllabusBulkCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_lecturer),
):
    """
    Bulk create syllabus entries for multiple weeks (up to 14 weeks).
    Only lecturers and super admins can create syllabus entries.
    """
    # Ensure course exists
    course = db.query(models.Course).filter(models.Course.id == bulk_in.course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check authorization
    if current_user.role == models.UserRole.LECTURER and course.lecturer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create syllabus for courses assigned to you"
        )
    
    # Check for existing active entries
    week_numbers = [week.week_number for week in bulk_in.weeks]
    existing_active = (
        db.query(models.Syllabus)
        .filter(
            models.Syllabus.course_id == bulk_in.course_id,
            models.Syllabus.week_number.in_(week_numbers),
            models.Syllabus.is_active == True
        )
        .all()
    )
    if existing_active:
        existing_weeks = [s.week_number for s in existing_active]
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Active syllabus already exists for weeks: {existing_weeks}. Use PUT to update."
        )
    
    # Create all syllabus entries
    created_entries = []
    for week_data in bulk_in.weeks:
        db_syllabus = models.Syllabus(
            course_id=bulk_in.course_id,
            week_number=week_data.week_number,
            topic=week_data.topic,
            content=week_data.content,
            version=1,
            is_active=True,
            created_by=current_user.id,
            change_reason=bulk_in.change_reason or "Bulk creation"
        )
        db.add(db_syllabus)
        created_entries.append(db_syllabus)
    
    db.commit()
    
    # Refresh all entries and format response
    result = []
    for entry in created_entries:
        db.refresh(entry, ['course', 'creator'])
        result.append(format_syllabus_response(entry))
    
    return result

@router.get("/{syllabus_id}", response_model=schemas.syllabus.SyllabusRead)
def get_syllabus(
    syllabus_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Get a specific syllabus entry by ID.
    Students can only view active entries.
    """
    syllabus_entry = db.query(models.Syllabus).filter(models.Syllabus.id == syllabus_id).first()
    if not syllabus_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Syllabus entry not found"
        )
    
    # Students can only see active entries
    if current_user.role == models.UserRole.STUDENT and not syllabus_entry.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view active syllabus entries"
        )
    
    # Load relationships
    db.refresh(syllabus_entry, ['course', 'creator'])
    
    return format_syllabus_response(syllabus_entry)

@router.put("/{syllabus_id}", response_model=schemas.syllabus.SyllabusRead)
def update_syllabus(
    syllabus_id: int,
    syllabus_in: schemas.syllabus.SyllabusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_lecturer),
):
    """
    Update a syllabus entry. This creates a new version while keeping the old version for history.
    Only lecturers and super admins can update syllabus entries.
    """
    # Fetch the existing record
    existing_syllabus = db.query(models.Syllabus).filter(models.Syllabus.id == syllabus_id).first()
    if not existing_syllabus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Syllabus entry not found"
        )
    
    # Check authorization
    course = existing_syllabus.course
    if current_user.role == models.UserRole.LECTURER and course.lecturer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update syllabus for courses assigned to you"
        )
    
    if not existing_syllabus.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update an inactive (historical) syllabus version. Use the active version."
        )
    
    # Validate week_number if being updated
    if syllabus_in.week_number is not None:
        # Check if new week_number already has an active entry
        if syllabus_in.week_number != existing_syllabus.week_number:
            existing_week = (
                db.query(models.Syllabus)
                .filter(
                    models.Syllabus.course_id == existing_syllabus.course_id,
                    models.Syllabus.week_number == syllabus_in.week_number,
                    models.Syllabus.is_active == True
                )
                .first()
            )
            if existing_week:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Active syllabus already exists for week {syllabus_in.week_number}"
                )
    
    # Start transaction logic for versioning
    try:
        # 1. Deactivate old record
        existing_syllabus.is_active = False
        
        # 2. Create new record with incremented version
        new_data = {
            'course_id': existing_syllabus.course_id,
            'week_number': syllabus_in.week_number if syllabus_in.week_number is not None else existing_syllabus.week_number,
            'topic': syllabus_in.topic if syllabus_in.topic is not None else existing_syllabus.topic,
            'content': syllabus_in.content if syllabus_in.content is not None else existing_syllabus.content,
            'version': existing_syllabus.version + 1,
            'is_active': True,
            'created_by': current_user.id,
            'change_reason': syllabus_in.change_reason or "Updated by lecturer"
        }
        
        new_syllabus = models.Syllabus(**new_data)
        db.add(new_syllabus)
        
        db.commit()
        db.refresh(new_syllabus)
        
        # Load relationships
        db.refresh(new_syllabus, ['course', 'creator'])
        
        return format_syllabus_response(new_syllabus)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Update failed: {str(e)}"
        )

@router.get("/{syllabus_id}/versions", response_model=List[schemas.syllabus.SyllabusRead])
def list_versions(
    syllabus_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Get version history for a syllabus entry.
    Students can only see active versions. Lecturers and admins see all versions.
    """
    # Find the original entry by id to get context
    base = db.query(models.Syllabus).filter(models.Syllabus.id == syllabus_id).first()
    if not base:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Syllabus entry not found"
        )
    
    query = (
        db.query(models.Syllabus)
        .filter(
            models.Syllabus.course_id == base.course_id,
            models.Syllabus.week_number == base.week_number,
        )
    )
    
    # Students only see active versions
    if current_user.role == models.UserRole.STUDENT:
        query = query.filter(models.Syllabus.is_active == True)
    
    versions = query.order_by(models.Syllabus.version.desc()).all()
    
    # Load relationships and format response
    result = []
    for version in versions:
        db.refresh(version, ['course', 'creator'])
        result.append(format_syllabus_response(version))
    
    return result

@router.delete("/{syllabus_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_syllabus(
    syllabus_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_lecturer),
):
    """
    Soft delete (deactivate) a syllabus entry.
    Only lecturers and super admins can delete syllabus entries.
    """
    syllabus_entry = db.query(models.Syllabus).filter(models.Syllabus.id == syllabus_id).first()
    if not syllabus_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Syllabus entry not found"
        )
    
    # Check authorization
    course = syllabus_entry.course
    if current_user.role == models.UserRole.LECTURER and course.lecturer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete syllabus for courses assigned to you"
        )
    
    # Soft delete: deactivate instead of hard delete
    syllabus_entry.is_active = False
    db.commit()
    return None

