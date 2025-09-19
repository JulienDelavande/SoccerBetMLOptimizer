# db/models/optim_results.py
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from base import Base

class OptimResult(Base):
    __tablename__ = "optim_results"
    __table_args__ = (
        sa.PrimaryKeyConstraint(
            "match_id", "model", "datetime_inference", "utility_fn", "datetime_optim",
            name="optim_results_pkey",
        ),
    )

    match_id: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    sport_key: Mapped[str | None] = mapped_column(sa.String(50))
    game: Mapped[str | None] = mapped_column(sa.String(100))
    date_match: Mapped[sa.Date | None] = mapped_column(sa.Date)
    time_match: Mapped[sa.Time | None] = mapped_column(sa.Time(timezone=False))
    home_team: Mapped[str | None] = mapped_column(sa.String(100))
    away_team: Mapped[str | None] = mapped_column(sa.String(100))

    model: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    datetime_inference: Mapped[sa.DateTime] = mapped_column(sa.TIMESTAMP(timezone=False), nullable=False)

    prob_home_win: Mapped[float | None] = mapped_column(sa.Float)
    prob_draw: Mapped[float | None] = mapped_column(sa.Float)
    prob_away_win: Mapped[float | None] = mapped_column(sa.Float)

    odds_home: Mapped[float | None] = mapped_column(sa.Float)
    odds_draw: Mapped[float | None] = mapped_column(sa.Float)
    odds_away: Mapped[float | None] = mapped_column(sa.Float)

    bookmaker_home: Mapped[str | None] = mapped_column(sa.String(100))
    bookmaker_draw: Mapped[str | None] = mapped_column(sa.String(100))
    bookmaker_away: Mapped[str | None] = mapped_column(sa.String(100))

    bookmaker_home_key: Mapped[str | None] = mapped_column(sa.String(50))
    bookmaker_draw_key: Mapped[str | None] = mapped_column(sa.String(50))
    bookmaker_away_key: Mapped[str | None] = mapped_column(sa.String(50))

    f_home: Mapped[float | None] = mapped_column(sa.Float)
    f_draw: Mapped[float | None] = mapped_column(sa.Float)
    f_away: Mapped[float | None] = mapped_column(sa.Float)

    datetime_optim: Mapped[sa.DateTime] = mapped_column(sa.TIMESTAMP(timezone=False), nullable=False)
    utility_fn: Mapped[str | None] = mapped_column(sa.String(255), server_default=sa.text("'Kelly'"))
    odds_home_datetime: Mapped[sa.DateTime | None] = mapped_column(sa.TIMESTAMP(timezone=False))
    odds_draw_datetime: Mapped[sa.DateTime | None] = mapped_column(sa.TIMESTAMP(timezone=False))
    odds_away_datetime: Mapped[sa.DateTime | None] = mapped_column(sa.TIMESTAMP(timezone=False))
    optim_label: Mapped[str | None] = mapped_column(sa.String(255), server_default=sa.text("'manual'"))
