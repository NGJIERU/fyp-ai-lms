"""merge demo

Revision ID: 148c292cd2e9
Revises: a1b2c3d4e5f6, add_performance_tables
Create Date: 2025-12-11 16:34:34.750718

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '148c292cd2e9'
down_revision: Union[str, None] = ('a1b2c3d4e5f6', 'add_performance_tables')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
