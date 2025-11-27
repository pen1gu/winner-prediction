from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.utils.model.db_model import Model as DBModel, TimestampMixin


class TeamModel(TimestampMixin, DBModel):
    __tablename__ = "teams"

    # 팀 이름
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    # 연고 국가
    country: Mapped[str | None] = mapped_column(String(128), default=None)

    # 소속 리그
    league: Mapped[str | None] = mapped_column(String(128), default=None)

    # 창단 연도
    founded: Mapped[int | None] = mapped_column(Integer, default=None)

    # 경기장 이름
    stadium: Mapped[str | None] = mapped_column(String(255), default=None)

    # 경기장 수용 인원
    stadium_capacity: Mapped[int | None] = mapped_column(Integer, default=None)

    # 경기장 위치
    stadium_location: Mapped[str | None] = mapped_column(String(255), default=None)

    # 경기장 주소
    stadium_address: Mapped[str | None] = mapped_column(String(255), default=None)

    # 경기장 도시
    stadium_city: Mapped[str | None] = mapped_column(String(128), default=None)

    # 소속 선수들
    players = relationship(
        "PlayerModel",
        back_populates="team",
        cascade="all, delete-orphan",
    )

    # 구단 소속 선수 상세 정보
    details = relationship(
        "PlayerDetailsModel",
        back_populates="team",
    )

    # 경기 영향 지표와의 관계
    match_affect_features = relationship(
        "PlayerMatchAffectFeaturesModel",
        back_populates="team",
    )

