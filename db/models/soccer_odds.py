# db/models/soccer_odds.py
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from base import Base

class SoccerOdd(Base):
    __tablename__ = "soccer_odds"
    __table_args__ = (
        sa.PrimaryKeyConstraint(
            "match_id", "bookmaker_key", "market_key", "outcome_name", "market_last_update",
            name="soccer_odds_pkey",
        ),
    )

    match_id: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    sport_key: Mapped[str | None] = mapped_column(sa.String(100))
    sport_title: Mapped[str | None] = mapped_column(sa.String(100))
    commence_time: Mapped[sa.DateTime | None] = mapped_column(sa.TIMESTAMP(timezone=False))
    home_team: Mapped[str | None] = mapped_column(sa.String(100))
    away_team: Mapped[str | None] = mapped_column(sa.String(100))
    bookmaker_key: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    bookmaker_title: Mapped[str | None] = mapped_column(sa.String(100))
    bookmaker_last_update: Mapped[sa.DateTime | None] = mapped_column(sa.TIMESTAMP(timezone=False))
    market_key: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    market_last_update: Mapped[sa.DateTime] = mapped_column(sa.TIMESTAMP(timezone=False), nullable=False)
    outcome_name: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    outcome_price: Mapped[sa.Numeric | None] = mapped_column(sa.Numeric(10, 2))
    datetime_insert: Mapped[sa.DateTime | None] = mapped_column(
        sa.TIMESTAMP(timezone=False), server_default=sa.text("CURRENT_TIMESTAMP")
    )
