"""add missing user columns

Revision ID: 3d54fa0e487f
Revises: e72131290341
Create Date: 2026-08-01 19:52:50.350836

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3d54fa0e487f'
down_revision: Union[str, Sequence[str], None] = 'e72131290341'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("users", sa.Column("state", nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    # Drop triggers and functions for email_verified
    op.drop_column("users", "state")