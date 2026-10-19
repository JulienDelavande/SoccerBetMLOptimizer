"""add bookmaker_link to soccer_odds

Revision ID: 3c1d2e4f5a6b
Revises: f7331373fa97
Create Date: 2026-10-19 15:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '3c1d2e4f5a6b'
down_revision: Union[str, Sequence[str], None] = 'f7331373fa97'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('soccer_odds', sa.Column('bookmaker_link', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('soccer_odds', 'bookmaker_link')
