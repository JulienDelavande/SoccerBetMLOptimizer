"""add waitlist table

Revision ID: c4e7a1b9d2f0
Revises: 7a2b9c4d1e3f
Create Date: 2026-11-15 12:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4e7a1b9d2f0"
down_revision: Union[str, Sequence[str], None] = "7a2b9c4d1e3f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "waitlist",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("plan", sa.String(length=10), nullable=False),
        sa.Column("budget", sa.String(length=10), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("lang", sa.String(length=5), server_default=sa.text("'fr'"), nullable=False),
        sa.Column("consent_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], name="fk_waitlist_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="waitlist_pkey"),
        sa.UniqueConstraint("email", name="uq_waitlist_email"),
        sa.CheckConstraint("email = lower(email)", name=op.f("ck_waitlist_email_lower")),
        sa.CheckConstraint("plan IN ('monthly', 'yearly', 'unsure')", name=op.f("ck_waitlist_plan")),
        sa.CheckConstraint("budget IN ('lt10', '10_20', '20_30', '30plus')", name=op.f("ck_waitlist_budget")),
        sa.CheckConstraint("char_length(message) <= 1000", name=op.f("ck_waitlist_message_len")),
    )
    op.create_index("ix_waitlist_user_id", "waitlist", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_waitlist_user_id", table_name="waitlist")
    op.drop_table("waitlist")
