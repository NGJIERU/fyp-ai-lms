"""
Database models for Student Performance Tracking
Tracks quiz attempts, weak topics, and learning progress
"""
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, ForeignKey, DateTime, Index, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class StudentEnrollment(Base):
    """
    Tracks student enrollment in courses.
    """
    __tablename__ = "student_enrollments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    student = relationship("User", foreign_keys=[student_id])
    course = relationship("Course")

    __table_args__ = (
        Index('ix_enrollment_student_course', 'student_id', 'course_id', unique=True),
    )


class QuizAttempt(Base):
    """
    Tracks individual quiz/assessment attempts.
    """
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    week_number = Column(Integer, nullable=False)
    question_type = Column(String(50), nullable=False)  # mcq, short_text, python_code, step_by_step
    question_data = Column(JSON, nullable=True)  # Store question details
    student_answer = Column(Text, nullable=True)
    score = Column(Float, nullable=False, default=0.0)
    max_score = Column(Float, nullable=False, default=1.0)
    is_correct = Column(Boolean, nullable=False, default=False)
    feedback = Column(Text, nullable=True)
    mode = Column(String(20), nullable=False, default="practice")  # practice or graded
    attempted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    time_spent_seconds = Column(Integer, nullable=True)  # Time spent on question
    
    # Relationships
    student = relationship("User", foreign_keys=[student_id])
    course = relationship("Course")

    __table_args__ = (
        Index('ix_quiz_attempts_student_course', 'student_id', 'course_id'),
        Index('ix_quiz_attempts_student_week', 'student_id', 'course_id', 'week_number'),
    )


class TopicPerformance(Base):
    """
    Aggregated performance per topic/week for a student.
    Updated after each quiz attempt.
    """
    __tablename__ = "topic_performance"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    week_number = Column(Integer, nullable=False)
    total_attempts = Column(Integer, default=0, nullable=False)
    correct_attempts = Column(Integer, default=0, nullable=False)
    average_score = Column(Float, default=0.0, nullable=False)
    last_attempt_at = Column(DateTime(timezone=True), nullable=True)
    is_weak_topic = Column(Boolean, default=False, nullable=False)  # Flagged as weak if score < threshold
    mastery_level = Column(String(20), default="not_started")  # not_started, learning, proficient, mastered
    
    # Relationships
    student = relationship("User", foreign_keys=[student_id])
    course = relationship("Course")

    __table_args__ = (
        Index('ix_topic_performance_student_course_week', 'student_id', 'course_id', 'week_number', unique=True),
        Index('ix_topic_performance_weak', 'student_id', 'is_weak_topic'),
    )


class LearningSession(Base):
    """
    Tracks learning sessions with the AI tutor.
    """
    __tablename__ = "learning_sessions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    week_number = Column(Integer, nullable=True)
    session_type = Column(String(50), nullable=False)  # explain, practice, review, chat
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    interactions_count = Column(Integer, default=0, nullable=False)
    materials_accessed = Column(JSON, nullable=True)  # List of material IDs accessed
    
    # Relationships
    student = relationship("User", foreign_keys=[student_id])
    course = relationship("Course")

    __table_args__ = (
        Index('ix_learning_sessions_student', 'student_id', 'started_at'),
    )


class TutorInteraction(Base):
    """
    Individual interactions with the AI tutor within a session.
    """
    __tablename__ = "tutor_interactions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("learning_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    interaction_type = Column(String(50), nullable=False)  # question, answer_check, hint_request, explanation
    user_input = Column(Text, nullable=True)
    tutor_response = Column(Text, nullable=True)
    context_used = Column(JSON, nullable=True)  # Material IDs used as context
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    session = relationship("LearningSession")
    student = relationship("User", foreign_keys=[student_id])

    __table_args__ = (
        Index('ix_tutor_interactions_session', 'session_id'),
    )


class ActivityLog(Base):
    """
    General activity logging for analytics.
    """
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(100), nullable=False)  # login, view_material, submit_quiz, etc.
    resource_type = Column(String(50), nullable=True)  # course, material, quiz, etc.
    resource_id = Column(Integer, nullable=True)
    extra_data = Column(JSON, nullable=True)  # Additional action-specific data
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index('ix_activity_logs_user_action', 'user_id', 'action'),
        Index('ix_activity_logs_created', 'created_at'),
    )
