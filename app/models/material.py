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
    url = Column(Text, unique=True, nullable=False, index=True)
    source = Column(String(100), nullable=False, index=True)  # e.g., "MIT OCW", "YouTube", "GitHub"
    type = Column(String(50), nullable=False)  # e.g., "pdf", "video", "repository", "blog", "article"
    author = Column(Text, nullable=True)
    publish_date = Column(DateTime(timezone=True), nullable=True)
    description = Column(Text, nullable=True)
    content_text = Column(Text, nullable=True)  # Full text content
    snippet = Column(Text, nullable=True)  # Short snippet for preview
    quality_score = Column(Float, nullable=False, default=0.0)
    content_hash = Column(String(64), nullable=False)  # SHA-256 hash for deduplication
    embedding = Column(JSON, nullable=True)  # Store embeddings as JSON-compatible array/object
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    topics = relationship("MaterialTopic", back_populates="material", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_materials_type', 'type'),
        Index('ix_materials_quality_score', 'quality_score'),
        Index('ix_materials_content_hash', 'content_hash'),
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

