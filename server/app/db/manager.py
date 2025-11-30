from __future__ import annotations

from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.utils.model.db_model import DBModel, TimestampMixin 

class ManagerModel(TimestampMixin, DBModel):
    __tablename__ = "manager"

    # FotMob ID
    fotmob_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # 감독 이름
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # 감독 나이
    age: Mapped[int | None] = mapped_column(Integer, default=None)

    # 감독 국가
    country: Mapped[str | None] = mapped_column(String(128), default=None)

    # 소속 팀
    team_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("teams.id", ondelete="SET NULL"), nullable=True
    )
    team = relationship("TeamModel", back_populates="manager")
