from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func, Boolean, Index, CheckConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base

class Syllabus(Base):
    __tablename__ = "syllabus"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    week_number = Column(Integer, nullable=False, index=True)
    topic = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    change_reason = Column(Text, nullable=True)

    # Relationships
    course = relationship("Course", back_populates="syllabus")
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        # Unique constraint: Only one active syllabus per course per week
        Index(
            "one_active_per_week",
            "course_id",
            "week_number",
            unique=True,
            postgresql_where=(is_active == True),
            sqlite_where=(is_active == True)
        ),
        # Check constraint: Week number must be between 1 and 14
        CheckConstraint('week_number BETWEEN 1 AND 14', name='check_week_number_range'),
        # Indexes for performance
        Index('ix_syllabus_course_week', 'course_id', 'week_number'),
    )

