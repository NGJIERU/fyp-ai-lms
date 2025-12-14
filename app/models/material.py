"""
Database models for Material Crawling & Repository module
"""
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, ForeignKey, DateTime, Index, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import JSON
from app.core.database import Base
import hashlib


class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False, index=True)
    url = Column(Text, nullable=True, index=True)  # Changed to nullable for uploaded files
    source = Column(String(100), nullable=False, index=True)  # e.g., "MIT OCW", "YouTube", "Manual Upload"
    type = Column(String(50), nullable=False)  # e.g., "pdf", "video", "repository", "blog", "article"
    
    # Material classification
    material_type = Column(String(20), nullable=False, default="crawled", index=True)  # "crawled" or "uploaded"
    
    # Original crawled material fields
    author = Column(Text, nullable=True)
    publish_date = Column(DateTime(timezone=True), nullable=True)
    description = Column(Text, nullable=True)
    content_text = Column(Text, nullable=True)  # Full text content
    snippet = Column(Text, nullable=True)  # Short snippet for preview
    quality_score = Column(Float, nullable=False, default=0.0)
    content_hash = Column(String(64), nullable=True)  # SHA-256 hash for deduplication (nullable for uploads)
    embedding = Column(JSON, nullable=True)  # Store embeddings as JSON-compatible array/object
    
    # Upload-specific fields (only for material_type="uploaded")
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    file_name = Column(String(255), nullable=True)  # Original filename
    file_path = Column(String(512), nullable=True, unique=True)  # Server storage path
    file_size = Column(Integer, nullable=True)  # File size in bytes
    content_type = Column(String(100), nullable=True)  # MIME type
    
    # Analytics (for both types)
    download_count = Column(Integer, default=0, nullable=False)
    view_count = Column(Integer, default=0, nullable=False)
    last_downloaded_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    topics = relationship("MaterialTopic", back_populates="material", cascade="all, delete-orphan")
    ratings = relationship("MaterialRating", back_populates="material", cascade="all, delete-orphan")
    uploader = relationship("User", foreign_keys=[uploaded_by])

    __table_args__ = (
        Index('ix_materials_type', 'type'),
        Index('ix_materials_material_type', 'material_type'),
        Index('ix_materials_quality_score', 'quality_score'),
        Index('ix_materials_uploaded_by', 'uploaded_by'),
        CheckConstraint('quality_score >= 0.0 AND quality_score <= 1.0', name='check_quality_score_range'),
    )

    @staticmethod
    def generate_content_hash(text: str) -> str:
        """Generate SHA-256 hash of content for deduplication"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()


class MaterialTopic(Base):
    __tablename__ = "material_topics"

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("materials.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    week_number = Column(Integer, nullable=False)
    relevance_score = Column(Float, nullable=False, default=0.0)
    approved_by_lecturer = Column(Boolean, default=False, nullable=False)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    material = relationship("Material", back_populates="topics")
    course = relationship("Course")
    approver = relationship("User", foreign_keys=[approved_by])

    __table_args__ = (
        Index('ix_material_topics_course_week', 'course_id', 'week_number'),
        Index('ix_material_topics_material', 'material_id'),
        CheckConstraint('week_number BETWEEN 1 AND 14', name='check_material_topic_week_range'),
        CheckConstraint('relevance_score >= 0.0 AND relevance_score <= 1.0', name='check_relevance_score_range'),
    )


class MaterialRating(Base):
    __tablename__ = "material_ratings"

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("materials.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)  # -1 or +1
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    material = relationship("Material", back_populates="ratings")
    student = relationship("User")

    __table_args__ = (
        Index('ix_material_ratings_material_student', 'material_id', 'student_id', unique=True),
        CheckConstraint('rating IN (-1, 1)', name='check_material_rating_value'),
    )


class CrawlLog(Base):
    __tablename__ = "crawl_logs"

    id = Column(Integer, primary_key=True, index=True)
    crawler_type = Column(String(50), nullable=False)  # e.g., "youtube", "github", "oer"
    status = Column(String(20), nullable=False, default="running")  # running, completed, failed
    items_fetched = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    finished_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index('ix_crawl_logs_crawler_type', 'crawler_type'),
        Index('ix_crawl_logs_status', 'status'),
    )

