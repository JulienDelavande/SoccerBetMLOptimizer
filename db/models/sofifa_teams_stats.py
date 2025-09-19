# db/models/sofifa_teams_stats.py
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from base import Base

class SofifaTeamStat(Base):
    __tablename__ = "sofifa_teams_stats"
    __table_args__ = (
        sa.PrimaryKeyConstraint("team", "update", name="unique_team_update"),
        sa.Index(
            "ix_sofifa_team_update_desc",
            "team",
            sa.text("update DESC"),
            postgresql_include=(
                "overall", "attack", "midfield", "defence",
                "transfer_budget", "club_worth"
            ),
        ),
    )


    league: Mapped[str | None] = mapped_column(sa.String(255))
    team: Mapped[str | None] = mapped_column(sa.String(255))
    overall: Mapped[int | None] = mapped_column(sa.Integer)
    attack: Mapped[int | None] = mapped_column(sa.Integer)
    midfield: Mapped[int | None] = mapped_column(sa.Integer)
    defence: Mapped[int | None] = mapped_column(sa.Integer)
    transfer_budget: Mapped[int | None] = mapped_column(sa.Integer)
    club_worth: Mapped[float | None] = mapped_column(sa.Float)

    build_up_speed: Mapped[str | None] = mapped_column(sa.String(255))
    build_up_dribbling: Mapped[str | None] = mapped_column(sa.String(255))
    build_up_passing: Mapped[str | None] = mapped_column(sa.String(255))
    build_up_positioning: Mapped[str | None] = mapped_column(sa.String(255))

    chance_creation_crossing: Mapped[str | None] = mapped_column(sa.String(255))
    chance_creation_passing: Mapped[str | None] = mapped_column(sa.String(255))
    chance_creation_shooting: Mapped[str | None] = mapped_column(sa.String(255))
    chance_creation_positioning: Mapped[str | None] = mapped_column(sa.String(255))

    defence_aggression: Mapped[str | None] = mapped_column(sa.String(255))
    defence_pressure: Mapped[str | None] = mapped_column(sa.String(255))
    defence_team_width: Mapped[str | None] = mapped_column(sa.String(255))
    defence_defender_line: Mapped[str | None] = mapped_column(sa.String(255))

    defence_domestic_prestige: Mapped[int | None] = mapped_column(sa.Integer)
    international_prestige: Mapped[int | None] = mapped_column(sa.Integer)
    players: Mapped[int | None] = mapped_column(sa.Integer)
    starting_xi_average_age: Mapped[float | None] = mapped_column(sa.Float)
    whole_team_average_age: Mapped[float | None] = mapped_column(sa.Float)
    fifa_edition: Mapped[str | None] = mapped_column(sa.String(255))
    update: Mapped[sa.DateTime | None] = mapped_column(sa.TIMESTAMP(timezone=False))
    datetime_insert: Mapped[sa.DateTime | None] = mapped_column(
        sa.TIMESTAMP(timezone=False), server_default=sa.text("CURRENT_TIMESTAMP")
    )
