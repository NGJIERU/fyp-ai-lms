from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import re

class CourseBase(BaseModel):
    code: str = Field(..., max_length=20, description="Course code (e.g., CS101, DS201)")
    name: str = Field(..., max_length=100, description="Course name")
    description: Optional[str] = Field(None, description="Course description")

    @validator('code')
    def validate_code_format(cls, v):
        """Validate course code format (alphanumeric, typically like CS101, DS201)"""
        # Allow flexible format: 2-6 alphanumeric characters, case-insensitive
        if not re.match(r'^[A-Z0-9]{2,10}$', v.upper()):
            raise ValueError('Course code must be 2-10 alphanumeric characters (e.g., CS101, DS201)')
        return v.upper()

class CourseCreate(CourseBase):
    lecturer_id: int = Field(..., description="ID of the lecturer assigned to this course")

class CourseUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    lecturer_id: Optional[int] = None

class CourseRead(CourseBase):
    id: int
    lecturer_id: Optional[int]
    lecturer_name: Optional[str] = Field(None, description="Name of the lecturer")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

