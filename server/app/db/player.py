from __future__ import annotations

from sqlalchemy import Integer, String, ForeignKey, Date, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.utils.model.db_model import DBModel, TimestampMixin


class PlayerModel(TimestampMixin, DBModel):
    __tablename__ = "player"

    # FotMob ID
    fotmob_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # 선수 이름
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # 나이
    age: Mapped[int | None] = mapped_column(Integer, default=None)

    # 소속 팀
    team_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("teams.id", ondelete="SET NULL")
    )
    team = relationship("TeamModel", back_populates="players")

    # 포지션 정보
    position: Mapped[list[str] | None] = mapped_column(JSON, default=list)

    # 역할 상세
    role: Mapped[dict | None] = mapped_column(JSON, default=dict)

    # 등번호
    shirt_number: Mapped[int | None] = mapped_column(Integer, default=None)

    # 키
    height: Mapped[int | None] = mapped_column(Integer, default=None)

    # 몸무게
    weight: Mapped[int | None] = mapped_column(Integer, default=None)

    # 생년월일
    birth_date: Mapped[str | None] = mapped_column(String(32), default=None)

    # 출생지
    birth_place: Mapped[str | None] = mapped_column(String(255), default=None)

    # 출생국
    birth_country: Mapped[str | None] = mapped_column(String(128), default=None)

    # 출생 지역
    birth_state: Mapped[str | None] = mapped_column(String(128), default=None)

    # 1:1 선수 상세 정보
    details = relationship(
        "PlayerDetailsModel",
        back_populates="player",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # 경기 영향 지표 컬렉션
    match_affect_features = relationship(
        "PlayerMatchAffectFeaturesModel",
        back_populates="player",
        cascade="all, delete-orphan",
    )

