# db/models/teams.py
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from base import Base

class Team(Base):
    __tablename__ = "teams"
    __table_args__ = (
        sa.UniqueConstraint("canonical_name", name="uq_teams_canonical_name"),
    )

    team_id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    canonical_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)

    aliases: Mapped[list["TeamAlias"]] = relationship(back_populates="team", cascade="all, delete-orphan")
