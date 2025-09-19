# db/models/fbref_results.py
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from base import Base


class FbrefResult(Base):
    __tablename__ = "fbref_results"
    __table_args__ = (
        sa.PrimaryKeyConstraint("game", name="fbref_results_pkey"),
        sa.Index("ix_fbref_date_not_null", "date", postgresql_where=sa.text("date IS NOT NULL")),
        sa.Index("ix_fbref_home_date", "home_team", "date"),
        sa.Index("ix_fbref_away_date", "away_team", "date"),
    )

    game: Mapped[str] = mapped_column(sa.Text, nullable=False)
    game_id: Mapped[str | None] = mapped_column(sa.Text)
    league: Mapped[str | None] = mapped_column(sa.Text)
    season: Mapped[str | None] = mapped_column(sa.Text)
    round: Mapped[str | None] = mapped_column(sa.Text)
    week: Mapped[int | None] = mapped_column(sa.Integer)
    day: Mapped[str | None] = mapped_column(sa.Text)
    date: Mapped[sa.Date | None] = mapped_column(sa.Date)
    time: Mapped[sa.Time | None] = mapped_column(sa.Time(timezone=False))
    home_team: Mapped[str | None] = mapped_column(sa.Text)
    home_xg: Mapped[float | None] = mapped_column(sa.Float)
    score: Mapped[str | None] = mapped_column(sa.Text)
    away_xg: Mapped[float | None] = mapped_column(sa.Float)
    away_team: Mapped[str | None] = mapped_column(sa.Text)
    attendance: Mapped[int | None] = mapped_column(sa.Integer)
    venue: Mapped[str | None] = mapped_column(sa.Text)
    referee: Mapped[str | None] = mapped_column(sa.Text)
    match_report: Mapped[str | None] = mapped_column(sa.Text)
    notes: Mapped[str | None] = mapped_column(sa.Text)
    index: Mapped[int | None] = mapped_column(sa.Integer)
    away_g: Mapped[int | None] = mapped_column(sa.Integer)  
    home_g: Mapped[int | None] = mapped_column(sa.Integer)
    away_sat: Mapped[int | None] = mapped_column(sa.Integer)
    home_sat: Mapped[int | None] = mapped_column(sa.Integer)
    datetime_insert: Mapped[sa.DateTime | None] = mapped_column(
        sa.TIMESTAMP(timezone=False),
        server_default=sa.text("CURRENT_TIMESTAMP")
    )
