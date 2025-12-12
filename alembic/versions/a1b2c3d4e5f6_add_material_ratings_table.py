"""add material ratings table

Revision ID: a1b2c3d4e5f6
Revises: 8e38b33c6342
Create Date: 2025-12-10 16:25:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "8e38b33c6342"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "material_ratings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("material_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["material_id"], ["materials.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.CheckConstraint("rating IN (-1, 1)", name="check_material_rating_value"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_material_ratings_material_student",
        "material_ratings",
        ["material_id", "student_id"],
        unique=True,
    )
    op.create_index(op.f("ix_material_ratings_material_id"), "material_ratings", ["material_id"], unique=False)
    op.create_index(op.f("ix_material_ratings_student_id"), "material_ratings", ["student_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_material_ratings_student_id"), table_name="material_ratings")
    op.drop_index(op.f("ix_material_ratings_material_id"), table_name="material_ratings")
    op.drop_index("ix_material_ratings_material_student", table_name="material_ratings")
    op.drop_table("material_ratings")
