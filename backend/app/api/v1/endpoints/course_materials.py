"""
API endpoints for Course Material Management
Allows lecturers to upload PDF materials and students to retrieve them
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
from datetime import datetime
from pathlib import Path

from app import models, schemas
from app.api import deps
from app.core.database import get_db

router = APIRouter()

# Configuration
UPLOAD_DIR = Path("/Users/jieru_0901/fyp_antigravity_5Dec_py/uploads/course_materials")
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes
ALLOWED_CONTENT_TYPES = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # DOCX
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # PPTX
    "application/zip",
    "application/x-zip-compressed",
]

# Ensure upload directory exists
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/{course_id}/materials/upload", response_model=schemas.material.MaterialRead, status_code=status.HTTP_201_CREATED)
async def upload_course_material(
    course_id: int,
    week_number: int = Form(..., ge=1, le=14, description="Week number (1-14)"),
    title: str = Form(..., min_length=1, max_length=255),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_lecturer),
):
    """
    Upload a PDF material for a specific week of a course. Only lecturers assigned to the course can upload.
    """
    # Verify course exists
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check authorization: Lecturer must be assigned to this course or be super admin
    if current_user.role == models.UserRole.LECTURER and course.lecturer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only upload materials for courses assigned to you"
        )
    
    # Validate content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Only PDF, DOCX, PPTX, and ZIP files are allowed. Received: {file.content_type}"
        )
    
    # Read file content to check size and save
    file_content = await file.read()
    file_size = len(file_content)
    
    # Validate file size
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size ({file_size} bytes) exceeds maximum allowed size ({MAX_FILE_SIZE} bytes)"
        )
    
    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty"
        )
    
    # Create course-specific directory
    course_dir = UPLOAD_DIR / str(course_id)
    course_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_extension}"
    file_path = course_dir / unique_filename
    
    # Save file
    try:
        with open(file_path, "wb") as f:
            f.write(file_content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    # Create database record
    db_material = models.Material(
        material_type="uploaded",
        source="Manual Upload",
        type=file.content_type.split('/')[-1] if '/' in file.content_type else "file",
        title=title,
        description=description,
        file_name=file.filename,
        file_path=str(file_path),
        file_size=file_size,
        content_type=file.content_type,
        uploaded_by=current_user.id,
        url=None,  # No external URL for uploaded files
        quality_score=1.0,  # Manually uploaded materials get highest score
    )
    db.add(db_material)
    db.flush()  # Get the material ID
    
    # Link material to course and week via MaterialTopic
    material_topic = models.MaterialTopic(
        material_id=db_material.id,
        course_id=course_id,
        week_number=week_number,
        relevance_score=1.0,  # Uploaded materials are fully relevant
        approved_by_lecturer=True,  # Auto-approve uploaded materials
        approved_at=datetime.utcnow()
    )
    db.add(material_topic)
    db.commit()
    db.refresh(db_material)
    
    # Prepare response with uploader name
    material_dict = {
        **db_material.__dict__,
        'uploader_name': current_user.full_name,
        'week_number': week_number  # Include week in response
    }
    return schemas.material.MaterialRead(**material_dict)


@router.get("/{course_id}/materials", response_model=List[schemas.material.MaterialRead])
def list_course_materials(
    course_id: int,
    week_number: Optional[int] = None,  # Optional filter by week
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    List all materials for a course, optionally filtered by week. Accessible by enrolled students and course lecturer.
    """
    # Verify course exists
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check authorization: User must be enrolled or be the lecturer or super admin
    if current_user.role == models.UserRole.STUDENT:
        enrollment = db.query(models.StudentEnrollment).filter(
            models.StudentEnrollment.student_id == current_user.id,
            models.StudentEnrollment.course_id == course_id,
            models.StudentEnrollment.is_active == True
        ).first()
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be enrolled in this course to view materials"
            )
    elif current_user.role == models.UserRole.LECTURER:
        if course.lecturer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view materials for courses assigned to you"
            )
    
    # Get materials via MaterialTopic (for uploaded materials linked to this course)
    query = db.query(models.MaterialTopic).filter(
        models.MaterialTopic.course_id == course_id
    )
    
    # Apply week filter if specified
    if week_number is not None:
        query = query.filter(models.MaterialTopic.week_number == week_number)
    
    material_topics = query.all()
    
    # Prepare response with uploader names and week numbers
    result = []
    for topic in material_topics:
        material = topic.material
        uploader = None
        if material.uploaded_by:
            uploader = db.query(models.User).filter(models.User.id == material.uploaded_by).first()
        
        material_dict = {
            **material.__dict__,
            'uploader_name': uploader.full_name if uploader else material.author,
            'course_id': course_id,
            'week_number': topic.week_number  # Include week number
        }
        result.append(schemas.material.MaterialRead(**material_dict))
    
    # Sort by week number, then by upload date
    result.sort(key=lambda m: (m.week_number if hasattr(m, 'week_number') else 0, m.created_at), reverse=True)
    
    return result


@router.get("/{course_id}/materials/{material_id}/download")
def download_course_material(
    course_id: int,
    material_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Download a specific course material. Accessible by enrolled students and course lecturer.
    """
    # Get material
    material = db.query(models.Material).filter(
        models.Material.id == material_id
    ).first()
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )
    
    # Verify course
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check authorization
    if current_user.role == models.UserRole.STUDENT:
        enrollment = db.query(models.StudentEnrollment).filter(
            models.StudentEnrollment.student_id == current_user.id,
            models.StudentEnrollment.course_id == course_id,
            models.StudentEnrollment.is_active == True
        ).first()
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be enrolled in this course to download materials"
            )
    elif current_user.role == models.UserRole.LECTURER:
        if course.lecturer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only download materials for courses assigned to you"
            )
    
    # Check if file exists
    if not os.path.exists(material.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server"
        )
    
    # Track download
    material.download_count += 1
    material.last_downloaded_at = datetime.utcnow()
    db.commit()
    
    # Return file
    return FileResponse(
        path=material.file_path,
        media_type=material.content_type,
        filename=material.file_name
    )


@router.put("/{course_id}/materials/{material_id}", response_model=schemas.material.MaterialRead)
def update_course_material(
    course_id: int,
    material_id: int,
    material_in: schemas.material.MaterialTopicCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_lecturer),
):
    """
    Update course material metadata. Only uploader or super admin can update.
    """
    # Get material
    material = db.query(models.CourseMaterial).filter(
        models.CourseMaterial.id == material_id,
        models.CourseMaterial.course_id == course_id
    ).first()
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )
    
    # Check authorization: Only uploader or super admin can update
    if current_user.role == models.UserRole.LECTURER and material.uploaded_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update materials you uploaded"
        )
    
    # Update fields
    update_data = material_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(material, field, value)
    
    db.commit()
    db.refresh(material)
    
    # Prepare response
    uploader = db.query(models.User).filter(models.User.id == material.uploaded_by).first()
    material_dict = {
        **material.__dict__,
        'uploader_name': uploader.full_name if uploader else None
    }
    return schemas.material.MaterialRead(**material_dict)


@router.delete("/{course_id}/materials/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course_material(
    course_id: int,
    material_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_lecturer),
):
    """
    Delete a course material. Only uploader or super admin can delete.
    """
    # Get material
    material = db.query(models.CourseMaterial).filter(
        models.CourseMaterial.id == material_id,
        models.CourseMaterial.course_id == course_id
    ).first()
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )
    
    # Check authorization
    if current_user.role == models.UserRole.LECTURER and material.uploaded_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete materials you uploaded"
        )
    
    # Delete file from storage
    try:
        if os.path.exists(material.file_path):
            os.remove(material.file_path)
    except Exception as e:
        # Log error but continue with database deletion
        print(f"Warning: Failed to delete file {material.file_path}: {str(e)}")
    
    # Delete database record
    db.delete(material)
    db.commit()
    
    return None


@router.post("/{course_id}/materials/upload-batch", response_model=List[schemas.material.MaterialRead], status_code=status.HTTP_201_CREATED)
async def upload_batch_materials(
    course_id: int,
    week_number: int = Form(..., ge=1, le=14, description="Week number (1-14)"),
    files: List[UploadFile] = File(...),
    titles: str = Form(...),  # JSON string array
    descriptions: Optional[str] = Form(None),  # JSON string array
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_lecturer),
):
    """
    Upload multiple materials at once to a specific week. Titles should be a JSON array matching the number of files.
    """
    import json
    
    # Parse titles and descriptions
    try:
        titles_list = json.loads(titles)
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Titles must be a valid JSON array"
        )
    
    descriptions_list = []
    if descriptions:
        try:
            descriptions_list = json.loads(descriptions)
        except:
            descriptions_list = [None] * len(files)
    else:
        descriptions_list = [None] * len(files)
    
    if len(titles_list) != len(files):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Number of titles ({len(titles_list)}) must match number of files ({len(files)})"
        )
    
    # Verify course exists
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check authorization
    if current_user.role == models.UserRole.LECTURER and course.lecturer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only upload materials for courses assigned to you"
        )
    
    # Create course-specific directory
    course_dir = UPLOAD_DIR / str(course_id)
    course_dir.mkdir(parents=True, exist_ok=True)
    
    created_materials = []
    
    # Process each file
    for idx, file in enumerate(files):
        title = titles_list[idx]
        description = descriptions_list[idx] if idx < len(descriptions_list) else None
        
        # Validate content type
        if file.content_type not in ALLOWED_CONTENT_TYPES:
            # Rollback on first error
            for created in created_materials:
                try:
                    if os.path.exists(str(created.file_path)):
                        os.remove(str(created.file_path))
                except:
                    pass
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"File '{file.filename}' has unsupported type: {file.content_type}"
            )
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Validate file size
        if file_size > MAX_FILE_SIZE or file_size == 0:
            for created in created_materials:
                try:
                    if os.path.exists(str(created.file_path)):
                        os.remove(str(created.file_path))
                except:
                    pass
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE if file_size > MAX_FILE_SIZE else status.HTTP_400_BAD_REQUEST,
                detail=f"File '{file.filename}' size issue"
            )
        
        # Generate unique filename
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_extension}"
        file_path = course_dir / unique_filename
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Create database record
        db_material = models.Material(
            material_type="uploaded",
            source="Manual Upload",
            type=file.content_type.split('/')[-1] if '/' in file.content_type else "file",
            title=title,
            description=description,
            file_name=file.filename,
            file_path=str(file_path),
            file_size=file_size,
            content_type=file.content_type,
            uploaded_by=current_user.id,
            url=None,
            quality_score=1.0,
        )
        db.add(db_material)
        created_materials.append(db_material)
    
    # Commit all at once
    db.commit()
    
    # Create MaterialTopic links for all materials
    for material in created_materials:
        db.refresh(material)
        material_topic = models.MaterialTopic(
            material_id=material.id,
            course_id=course_id,
            week_number=week_number,
            relevance_score=1.0,
            approved_by_lecturer=True,
            approved_at=datetime.utcnow()
        )
        db.add(material_topic)
    db.commit()
    
    # Prepare response
    result = []
    for material in created_materials:
        material_dict = {
            **material.__dict__,
            'uploader_name': current_user.full_name,
            'week_number': week_number
        }
        result.append(schemas.material.MaterialRead(**material_dict))
    
    return result

