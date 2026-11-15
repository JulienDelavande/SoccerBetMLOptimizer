# db/models/waitlist.py
import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from base import Base


class WaitlistEntry(Base):
    """Visitors who asked to hear about the paid offer's launch (no payment, no account needed)."""
    __tablename__ = "waitlist"
    __table_args__ = (
        sa.UniqueConstraint("email", name="uq_waitlist_email"),
        sa.CheckConstraint("email = lower(email)", name="email_lower"),
        sa.CheckConstraint("plan IN ('monthly', 'yearly', 'unsure')", name="plan"),
        sa.CheckConstraint("budget IN ('lt10', '10_20', '20_30', '30plus')", name="budget"),
        sa.CheckConstraint("char_length(message) <= 1000", name="message_len"),
        sa.Index("ix_waitlist_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(sa.String(320), nullable=False)  # stored lowercased
    # Linked only when the visitor was signed in with this same email; account deletion removes the row.
    user_id: Mapped[int | None] = mapped_column(sa.ForeignKey("users.user_id", ondelete="CASCADE"))
    plan: Mapped[str] = mapped_column(sa.String(10), nullable=False)    # monthly | yearly | unsure
    budget: Mapped[str] = mapped_column(sa.String(10), nullable=False)  # lt10 | 10_20 | 20_30 | 30plus
    message: Mapped[str | None] = mapped_column(sa.Text)
    lang: Mapped[str] = mapped_column(sa.String(5), nullable=False, server_default=sa.text("'fr'"))
    consent_at: Mapped[datetime.datetime] = mapped_column(sa.TIMESTAMP(timezone=True), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime.datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"))
