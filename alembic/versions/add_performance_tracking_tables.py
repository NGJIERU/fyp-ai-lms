"""Add performance tracking tables

Revision ID: add_performance_tables
Revises: 8e38b33c6342
Create Date: 2024-12-09

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_performance_tables'
down_revision = '8e38b33c6342'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create student_enrollments table
    op.create_table(
        'student_enrollments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('enrolled_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_enrollment_student_course', 'student_enrollments', ['student_id', 'course_id'], unique=True)
    op.create_index('ix_student_enrollments_student_id', 'student_enrollments', ['student_id'])
    op.create_index('ix_student_enrollments_course_id', 'student_enrollments', ['course_id'])

    # Create quiz_attempts table
    op.create_table(
        'quiz_attempts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('week_number', sa.Integer(), nullable=False),
        sa.Column('question_type', sa.String(50), nullable=False),
        sa.Column('question_data', sa.JSON(), nullable=True),
        sa.Column('student_answer', sa.Text(), nullable=True),
        sa.Column('score', sa.Float(), nullable=False, default=0.0),
        sa.Column('max_score', sa.Float(), nullable=False, default=1.0),
        sa.Column('is_correct', sa.Boolean(), nullable=False, default=False),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('mode', sa.String(20), nullable=False, default='practice'),
        sa.Column('attempted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('time_spent_seconds', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_quiz_attempts_student_course', 'quiz_attempts', ['student_id', 'course_id'])
    op.create_index('ix_quiz_attempts_student_week', 'quiz_attempts', ['student_id', 'course_id', 'week_number'])
    op.create_index('ix_quiz_attempts_id', 'quiz_attempts', ['id'])

    # Create topic_performance table
    op.create_table(
        'topic_performance',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('week_number', sa.Integer(), nullable=False),
        sa.Column('total_attempts', sa.Integer(), nullable=False, default=0),
        sa.Column('correct_attempts', sa.Integer(), nullable=False, default=0),
        sa.Column('average_score', sa.Float(), nullable=False, default=0.0),
        sa.Column('last_attempt_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_weak_topic', sa.Boolean(), nullable=False, default=False),
        sa.Column('mastery_level', sa.String(20), nullable=False, default='not_started'),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_topic_performance_student_course_week', 'topic_performance', ['student_id', 'course_id', 'week_number'], unique=True)
    op.create_index('ix_topic_performance_weak', 'topic_performance', ['student_id', 'is_weak_topic'])
    op.create_index('ix_topic_performance_id', 'topic_performance', ['id'])

    # Create learning_sessions table
    op.create_table(
        'learning_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('week_number', sa.Integer(), nullable=True),
        sa.Column('session_type', sa.String(50), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('interactions_count', sa.Integer(), nullable=False, default=0),
        sa.Column('materials_accessed', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_learning_sessions_student', 'learning_sessions', ['student_id', 'started_at'])
    op.create_index('ix_learning_sessions_id', 'learning_sessions', ['id'])

    # Create tutor_interactions table
    op.create_table(
        'tutor_interactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('interaction_type', sa.String(50), nullable=False),
        sa.Column('user_input', sa.Text(), nullable=True),
        sa.Column('tutor_response', sa.Text(), nullable=True),
        sa.Column('context_used', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['learning_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_tutor_interactions_session', 'tutor_interactions', ['session_id'])
    op.create_index('ix_tutor_interactions_id', 'tutor_interactions', ['id'])

    # Create activity_logs table
    op.create_table(
        'activity_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=True),
        sa.Column('resource_id', sa.Integer(), nullable=True),
        sa.Column('extra_data', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('user_agent', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_activity_logs_user_action', 'activity_logs', ['user_id', 'action'])
    op.create_index('ix_activity_logs_created', 'activity_logs', ['created_at'])
    op.create_index('ix_activity_logs_id', 'activity_logs', ['id'])


def downgrade() -> None:
    op.drop_table('activity_logs')
    op.drop_table('tutor_interactions')
    op.drop_table('learning_sessions')
    op.drop_table('topic_performance')
    op.drop_table('quiz_attempts')
    op.drop_table('student_enrollments')
