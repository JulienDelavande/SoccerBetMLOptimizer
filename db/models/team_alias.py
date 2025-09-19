# db/models/team_alias.py
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship, foreign
from base import Base

class TeamAlias(Base):
    __tablename__ = "team_alias"
    __table_args__ = (
        sa.PrimaryKeyConstraint("source", "raw_name", name="team_alias_pkey"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.team_id"], name="fk_team_alias_team_id_teams"),
        sa.Index("ix_team_alias_team_id", "team_id"),
    )

    source: Mapped[str] = mapped_column(sa.String(32), nullable=False)      # 'sofifa' | 'fbref' | etc.
    raw_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)   # exact dans la source
    team_id: Mapped[int] = mapped_column(sa.Integer, nullable=False)

    team: Mapped["Team"] = relationship(back_populates="aliases")
