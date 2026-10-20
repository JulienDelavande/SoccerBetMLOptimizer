# db/models/users.py
import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (sa.UniqueConstraint("google_sub", name="uq_users_google_sub"),)

    user_id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    google_sub: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(sa.String(320))
    name: Mapped[str | None] = mapped_column(sa.String(255))
    avatar_url: Mapped[str | None] = mapped_column(sa.Text)
    created_at: Mapped[datetime.datetime] = mapped_column(
        sa.TIMESTAMP(timezone=False), server_default=sa.text("CURRENT_TIMESTAMP"))

    settings: Mapped["UserSettings"] = relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)
    bets: Mapped[list["UserBet"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserSettings(Base):
    __tablename__ = "user_settings"

    user_id: Mapped[int] = mapped_column(sa.ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    bankroll: Mapped[float] = mapped_column(sa.Float, nullable=False, server_default=sa.text("1000"))
    # prudent / balanced / aggressive -> quarter / half / full Kelly in the backend.
    risk_preset: Mapped[str] = mapped_column(sa.String(20), nullable=False, server_default=sa.text("'balanced'"))
    # Bookmaker keys the user has an account at; empty array = every book (site default).
    books: Mapped[list[str]] = mapped_column(sa.ARRAY(sa.Text), nullable=False, server_default=sa.text("'{}'"))
    min_edge: Mapped[float | None] = mapped_column(sa.Float)  # optional personal override
    alerts_enabled: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=sa.text("false"))
    telegram_chat_id: Mapped[str | None] = mapped_column(sa.String(64))
    # Short-lived code the user sends to the bot (/start <code>) to link their chat.
    telegram_link_code: Mapped[str | None] = mapped_column(sa.String(32))
    updated_at: Mapped[datetime.datetime] = mapped_column(
        sa.TIMESTAMP(timezone=False), server_default=sa.text("CURRENT_TIMESTAMP"))

    user: Mapped["User"] = relationship(back_populates="settings")


class UserBet(Base):
    __tablename__ = "user_bets"
    __table_args__ = (sa.PrimaryKeyConstraint("user_id", "match_id", "side", name="user_bets_pkey"),)

    user_id: Mapped[int] = mapped_column(sa.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    match_id: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    side: Mapped[str] = mapped_column(sa.String(10), nullable=False)  # home / draw / away
    recommended_price: Mapped[float | None] = mapped_column(sa.Float)
    placed_price: Mapped[float | None] = mapped_column(sa.Float)  # actual odds taken, optional
    stake: Mapped[float | None] = mapped_column(sa.Float)  # euros staked
    status: Mapped[str] = mapped_column(sa.String(10), nullable=False, server_default=sa.text("'placed'"))
    settled_gain: Mapped[float | None] = mapped_column(sa.Float)  # euros won/lost once settled
    created_at: Mapped[datetime.datetime] = mapped_column(
        sa.TIMESTAMP(timezone=False), server_default=sa.text("CURRENT_TIMESTAMP"))

    user: Mapped["User"] = relationship(back_populates="bets")
