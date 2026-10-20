"""add user, user_settings, user_bets tables

Revision ID: 7a2b9c4d1e3f
Revises: 3c1d2e4f5a6b
Create Date: 2026-10-20 12:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7a2b9c4d1e3f"
down_revision: Union[str, Sequence[str], None] = "3c1d2e4f5a6b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("user_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("google_sub", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=False), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("user_id", name="users_pkey"),
        sa.UniqueConstraint("google_sub", name="uq_users_google_sub"),
    )
    op.create_table(
        "user_settings",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("bankroll", sa.Float(), server_default=sa.text("1000"), nullable=False),
        sa.Column("risk_preset", sa.String(length=20), server_default=sa.text("'balanced'"), nullable=False),
        sa.Column("books", sa.ARRAY(sa.Text()), server_default=sa.text("'{}'"), nullable=False),
        sa.Column("min_edge", sa.Float(), nullable=True),
        sa.Column("alerts_enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("telegram_chat_id", sa.String(length=64), nullable=True),
        sa.Column("telegram_link_code", sa.String(length=32), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=False), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], name="fk_user_settings_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", name="user_settings_pkey"),
    )
    op.create_table(
        "user_bets",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("match_id", sa.String(length=50), nullable=False),
        sa.Column("side", sa.String(length=10), nullable=False),
        sa.Column("recommended_price", sa.Float(), nullable=True),
        sa.Column("placed_price", sa.Float(), nullable=True),
        sa.Column("stake", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=10), server_default=sa.text("'placed'"), nullable=False),
        sa.Column("settled_gain", sa.Float(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=False), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], name="fk_user_bets_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "match_id", "side", name="user_bets_pkey"),
    )
    op.create_index("ix_user_bets_user_id", "user_bets", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_user_bets_user_id", table_name="user_bets")
    op.drop_table("user_bets")
    op.drop_table("user_settings")
    op.drop_table("users")
