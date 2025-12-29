from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel, HttpUrl
import os, shutil
import httpx
from bs4 import BeautifulSoup
from openai import OpenAI
import json

from app.core.database import get_db
from app.core.config import settings
from app import models, schemas
from app.api import deps

router = APIRouter()

# Directory for uploaded files (local for now)
UPLOAD_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../media/lecturer_materials"))
os.makedirs(UPLOAD_ROOT, exist_ok=True)

# Initialize OpenAI client
openai_client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None

# Request/Response models for URL analysis
class URLAnalysisRequest(BaseModel):
    url: HttpUrl

class URLAnalysisResponse(BaseModel):
    title: str
    description: str
    type: str
    confidence: float

@router.post("/analyze-url", response_model=URLAnalysisResponse)
async def analyze_url(
    request: URLAnalysisRequest,
    current_user: models.User = Depends(deps.get_current_lecturer),
):
    """
    Analyze a URL and extract metadata using AI.
    Fetches the page content and uses OpenAI to suggest title, description, and type.
    """
    if not openai_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not configured. Please set OPENAI_API_KEY.",
        )
    
    try:
        url_str = str(request.url)
        
        # Fetch URL content
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(url_str, headers={
                "User-Agent": "Mozilla/5.0 (compatible; AI-LMS-Bot/1.0)"
            })
            response.raise_for_status()
            html_content = response.text
        
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract basic metadata
        page_title = soup.find('title')
        page_title_text = page_title.get_text().strip() if page_title else ""
        
        meta_description = soup.find('meta', attrs={'name': 'description'})
        meta_desc_text = meta_description.get('content', '').strip() if meta_description else ""
        
        # Get first paragraph or visible text
        paragraphs = soup.find_all('p', limit=5)
        page_text = ' '.join([p.get_text().strip() for p in paragraphs])[:1000]
        
        # Prepare content for AI analysis
        content_summary = f"""
URL: {url_str}
Page Title: {page_title_text}
Meta Description: {meta_desc_text}
Content Preview: {page_text[:500]}
"""
        
        # Use OpenAI to analyze and suggest metadata
        ai_response = openai_client.chat.completions.create(
            model=settings.AI_TUTOR_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": """You are an educational content analyzer. Given a URL and its content, extract:
1. A clear, concise title (max 100 chars)
2. A helpful description for students (max 200 chars)
3. The material type: one of [pdf, ppt, video, article, exercise, dataset]

Respond in JSON format:
{
  "title": "...",
  "description": "...",
  "type": "..."
}"""
                },
                {
                    "role": "user",
                    "content": content_summary
                }
            ],
            temperature=0.3,
            max_tokens=300
        )
        
        # Parse AI response
        ai_result = json.loads(ai_response.choices[0].message.content)
        
        return URLAnalysisResponse(
            title=ai_result.get("title", page_title_text)[:100],
            description=ai_result.get("description", meta_desc_text)[:200],
            type=ai_result.get("type", "article"),
            confidence=0.85  # Could be calculated based on content quality
        )
        
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch URL: {str(e)}"
        )
    except json.JSONDecodeError:
        # Fallback if AI doesn't return valid JSON
        return URLAnalysisResponse(
            title=page_title_text[:100] if page_title_text else "Untitled Resource",
            description=meta_desc_text[:200] if meta_desc_text else "No description available",
            type="article",
            confidence=0.5
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )

@router.post("/", response_model=schemas.material.MaterialResponse)
async def upload_material(
    title: str = Form(...),
    description: str = Form(None),
    course_id: int = Form(...),
    type: str = Form(...),
    week_number: int = Form(...),  # NEW: Week number for MaterialTopic
    file: UploadFile = File(None),  # Now optional
    url: str = Form(None),  # NEW: URL field
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_lecturer),
):
    try:
        # Validate: must have either file OR URL
        if not file and not url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please provide either a file or a URL",
            )
        if file and url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please provide either a file OR a URL, not both",
            )
        
        # Validate week_number range
        if week_number < 1 or week_number > 14:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Week number must be between 1 and 14",
            )
        
        # Verify ownership of the course
        course = db.query(models.Course).filter(models.Course.id == course_id).first()
        if not course or course.lecturer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Course not owned by lecturer",
            )

        # Initialize material data
        material_data = {
            "title": title,
            "description": description,
            "source": "Manual Upload",
            "type": type,
            "material_type": "uploaded",
            "uploaded_by": current_user.id,
        }

        # Handle file upload
        if file:
            ext = os.path.splitext(file.filename)[1]
            safe_name = f"material_{current_user.id}_{int(datetime.utcnow().timestamp())}{ext}"
            file_path = os.path.join(UPLOAD_ROOT, safe_name)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            material_data.update({
                "url": f"/lecturer/materials/{safe_name}",
                "file_name": file.filename,
                "file_path": file_path,
                "file_size": os.path.getsize(file_path),
                "content_type": file.content_type,
            })
        # Handle URL
        elif url:
            material_data.update({
                "url": url,
                "file_name": None,
                "file_path": None,
                "file_size": None,
                "content_type": None,
            })

        # Create DB record
        material = models.Material(**material_data)
        db.add(material)
        db.commit()
        db.refresh(material)
        
        # Create MaterialTopic link to associate material with course week
        material_topic = models.MaterialTopic(
            material_id=material.id,
            course_id=course_id,
            week_number=week_number,
            relevance_score=1.0,  # Manual uploads are 100% relevant
            approved_by_lecturer=True,  # Auto-approve lecturer uploads
            approved_at=datetime.utcnow(),
            approved_by=current_user.id,
        )
        db.add(material_topic)
        db.commit()
        db.refresh(material_topic)
        
        return material
    except HTTPException:
        raise
    except Exception as e:
        print(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/{filename}")
async def serve_material(filename: str):
    file_path = os.path.join(UPLOAD_ROOT, filename)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)
