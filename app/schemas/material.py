"""
Pydantic schemas for Material Crawling & Repository module
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class MaterialType(str, Enum):
    PDF = "pdf"
    PPT = "ppt"
    VIDEO = "video"
    ARTICLE = "article"
    REPOSITORY = "repository"
    BLOG = "blog"
    DATASET = "dataset"
    EXERCISE = "exercise"


class MaterialSource(str, Enum):
    MIT_OCW = "MIT OCW"
    NPTEL = "NPTEL"
    YOUTUBE = "YouTube"
    GITHUB = "GitHub"
    ARXIV = "arXiv"
    PUBMED = "PubMed"
    FREECODECAMP = "freeCodeCamp"
    GEEKSFORGEEKS = "GeeksforGeeks"
    REALPYTHON = "RealPython"
    KAGGLE = "Kaggle"
    UCI = "UCI ML Repository"
    OTHER = "Other"


class MaterialBase(BaseModel):
    title: str = Field(..., description="Material title")
    url: str = Field(..., description="Material URL")
    source: str = Field(..., description="Source name")
    type: MaterialType = Field(..., description="Material type")
    author: Optional[str] = Field(None, description="Author name")
    publish_date: Optional[datetime] = Field(None, description="Publish date")
    description: Optional[str] = Field(None, description="Description")
    content_text: Optional[str] = Field(None, description="Full text content")
    snippet: Optional[str] = Field(None, description="Preview snippet")


class MaterialCreate(MaterialBase):
    quality_score: float = Field(0.0, ge=0.0, le=1.0, description="Quality score")
    embedding: Optional[List[float]] = Field(None, description="Embedding vector")


class MaterialUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content_text: Optional[str] = None
    snippet: Optional[str] = None
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)


class MaterialRead(MaterialBase):
    id: int
    quality_score: float
    created_at: datetime
    updated_at: datetime
    topics_count: Optional[int] = Field(None, description="Number of course topics this material is mapped to")

    class Config:
        from_attributes = True


class MaterialTopicCreate(BaseModel):
    material_id: int
    course_id: int
    week_number: int = Field(..., ge=1, le=14)
    relevance_score: float = Field(0.0, ge=0.0, le=1.0)


class MaterialTopicRead(BaseModel):
    id: int
    material_id: int
    course_id: int
    week_number: int
    relevance_score: float
    approved_by_lecturer: bool
    approved_at: Optional[datetime]
    material: Optional[MaterialRead] = None
    course_name: Optional[str] = None

    class Config:
        from_attributes = True


class MaterialTopicApprove(BaseModel):
    approved: bool = True


class CrawlRequest(BaseModel):
    crawler_type: Optional[str] = Field(None, description="Specific crawler type, or None for all")
    max_items: Optional[int] = Field(100, ge=1, le=1000, description="Maximum items to crawl")


class CrawlResponse(BaseModel):
    status: str
    crawler_type: str
    items_fetched: int
    message: str
    log_id: Optional[int] = None


class MaterialSearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    limit: int = Field(10, ge=1, le=100)
    min_quality: float = Field(0.45, ge=0.0, le=1.0)
    course_id: Optional[int] = None
    week_number: Optional[int] = Field(None, ge=1, le=14)


class MaterialSearchResult(BaseModel):
    material: MaterialRead
    similarity_score: float
    relevance_score: Optional[float] = None


class MaterialRatingBase(BaseModel):
    rating: int = Field(..., description="Thumbs up (+1) or thumbs down (-1)", ge=-1, le=1)
    note: Optional[str] = Field(None, max_length=1000, description="Optional note about the rating")


class MaterialRatingCreate(MaterialRatingBase):
    pass


class MaterialRatingRead(MaterialRatingBase):
    id: int
    material_id: int
    student_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MaterialRatingSummary(BaseModel):
    material_id: int
    average_rating: float
    total_ratings: int
    upvotes: int
    downvotes: int


class MaterialRatingInsight(MaterialRatingSummary):
    title: str
    course_id: int
    course_name: Optional[str] = None


class MaterialResponse(MaterialRead):
    material_type: str = Field(..., description="Type of material (uploaded/crawled)")
    uploaded_by: Optional[int] = Field(None, description="ID of the uploader")
    file_name: Optional[str] = Field(None, description="Original filename")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    content_type: Optional[str] = Field(None, description="MIME type")

