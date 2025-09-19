# db/models/models_results.py
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from base import Base

class ModelsResult(Base):
    __tablename__ = "models_results"
    __table_args__ = (
        sa.PrimaryKeyConstraint(
            "datetime_inference", "model", "game",
            name="models_results_datetime_inference_model_game_key",
        ),
    )

    datetime_inference: Mapped[sa.DateTime] = mapped_column(sa.TIMESTAMP(timezone=False), nullable=False)
    model: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    game_id: Mapped[str | None] = mapped_column(sa.String(255))
    game: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    date_match: Mapped[sa.Date] = mapped_column(sa.Date, nullable=False)
    time_match: Mapped[sa.Time | None] = mapped_column(sa.Time(timezone=False))
    home_team: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    away_team: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    prob_home_win: Mapped[float | None] = mapped_column(sa.Float)
    prob_draw: Mapped[float | None] = mapped_column(sa.Float)
    prob_away_win: Mapped[float | None] = mapped_column(sa.Float)
    prob_home_team_score: Mapped[float | None] = mapped_column(sa.Float)
    prob_away_team_score: Mapped[float | None] = mapped_column(sa.Float)
