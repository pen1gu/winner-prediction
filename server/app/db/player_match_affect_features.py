from __future__ import annotations

from sqlalchemy import Integer, ForeignKey, Float, Boolean, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.utils.model.db_model import Model as DBModel, TimestampMixin


class PlayerMatchAffectFeaturesModel(TimestampMixin, DBModel):
    __tablename__ = "player_match_affect_features"

    # 선수 FK
    player_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False
    )

    # 팀 FK
    team_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("teams.id", ondelete="SET NULL"), nullable=True
    )

    # 성적 추이
    performance_trend: Mapped[list[dict] | None] = mapped_column(JSON, default=None)

    # 부상 이력
    injury_history: Mapped[list[dict] | None] = mapped_column(JSON, default=None)

    # 현재 폼
    current_form: Mapped[str | None] = mapped_column(String(32), default=None)

    # 폼 점수
    form_rating: Mapped[float | None] = mapped_column(Float, default=None)

    # 최근 경기 기록
    recent_matches: Mapped[list[dict] | None] = mapped_column(JSON, default=None)

    # 출전 가능 여부
    availability_status: Mapped[str | None] = mapped_column(String(64), default=None)

    # 국가대표 출전 횟수
    national_team_caps: Mapped[int | None] = mapped_column(Integer, default=None)

    # 최근 국가대표 출장 여부
    recently_played_national_team: Mapped[bool | None] = mapped_column(
        Boolean, default=None
    )

    # 출전 시간 통계
    playing_time_stats: Mapped[dict | None] = mapped_column(JSON, default=None)

    # 동료 대비 비교 지표
    comparison_with_peers: Mapped[dict | None] = mapped_column(JSON, default=None)

    # 선수 관계
    player = relationship("PlayerModel", back_populates="match_affect_features")

    # 팀 관계
    team = relationship("TeamModel", back_populates="match_affect_features")

