from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class SyllabusBase(BaseModel):
    week_number: int = Field(..., ge=1, le=14, description="Week number (1-14)")
    topic: str = Field(..., max_length=255, description="Week topic title")
    content: Optional[str] = Field(None, description="Detailed content/description for the week")

    @validator('week_number')
    def validate_week_number(cls, v):
        if not (1 <= v <= 14):
            raise ValueError('Week number must be between 1 and 14')
        return v

class SyllabusCreate(SyllabusBase):
    course_id: int = Field(..., description="ID of the course this syllabus belongs to")
    change_reason: Optional[str] = Field(None, description="Reason for creating this syllabus entry")

class SyllabusUpdate(BaseModel):
    week_number: Optional[int] = Field(None, ge=1, le=14)
    topic: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = None
    change_reason: Optional[str] = None

class SyllabusRead(SyllabusBase):
    id: int
    course_id: int
    version: int
    is_active: bool
    created_by: int
    created_by_name: Optional[str] = Field(None, description="Name of the user who created this")
    course_name: Optional[str] = Field(None, description="Name of the course")
    created_at: datetime
    change_reason: Optional[str]

    class Config:
        from_attributes = True

class SyllabusBulkCreate(BaseModel):
    """Schema for bulk creating 14-week syllabus"""
    course_id: int
    weeks: List[SyllabusBase] = Field(..., min_items=1, max_items=14, description="List of week syllabus entries")
    change_reason: Optional[str] = Field(None, description="Reason for bulk creation")

    @validator('weeks')
    def validate_weeks(cls, v):
        """Ensure no duplicate week numbers and all weeks are 1-14"""
        week_numbers = [week.week_number for week in v]
        if len(week_numbers) != len(set(week_numbers)):
            raise ValueError('Duplicate week numbers found')
        if not all(1 <= w <= 14 for w in week_numbers):
            raise ValueError('All week numbers must be between 1 and 14')
        return v

