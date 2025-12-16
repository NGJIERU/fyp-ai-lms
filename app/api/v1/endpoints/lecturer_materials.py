from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime
import os, shutil

from app.core.database import get_db
from app import models, schemas
from app.api import deps

router = APIRouter(prefix="/lecturer/materials", tags=["Lecturer Materials"])

# Directory for uploaded files (local for now)
UPLOAD_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../media/lecturer_materials"))
os.makedirs(UPLOAD_ROOT, exist_ok=True)

@router.post("/", response_model=schemas.material.MaterialResponse)
async def upload_material(
    title: str = Form(...),
    description: str = Form(None),
    course_id: int = Form(...),
    type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_lecturer),
):
    # Verify ownership of the course
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course or course.lecturer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Course not owned by lecturer",
        )

    # Save file locally
    ext = os.path.splitext(file.filename)[1]
    safe_name = f"material_{current_user.id}_{int(datetime.utcnow().timestamp())}{ext}"
    file_path = os.path.join(UPLOAD_ROOT, safe_name)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Create DB record (material_type = "uploaded")
    material = models.Material(
        title=title,
        description=description,
        source="Manual Upload",
        type=type,
        url=f"/lecturer/materials/{safe_name}",
        material_type="uploaded",
        uploaded_by=current_user.id,
        file_name=file.filename,
        file_path=file_path,
        file_size=os.path.getsize(file_path),
        content_type=file.content_type,
    )
    db.add(material)
    db.commit()
    db.refresh(material)
    return material

@router.get("/{filename}")
async def serve_material(filename: str):
    file_path = os.path.join(UPLOAD_ROOT, filename)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)
