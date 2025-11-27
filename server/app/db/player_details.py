from __future__ import annotations

from sqlalchemy import Integer, ForeignKey, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.utils.model.db_model import Model as DBModel, TimestampMixin


class PlayerDetailsModel(TimestampMixin, DBModel):
    __tablename__ = "player_details"

    # 선수 FK
    player_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("players.id", ondelete="CASCADE"), unique=True
    )

    # 팀 FK
    team_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("teams.id", ondelete="SET NULL"), nullable=True
    )

    # 시장 가치 추이
    market_value_history: Mapped[list[dict] | None] = mapped_column(JSON, default=None)

    # 현재 시장 가치
    current_market_value: Mapped[int | None] = mapped_column(Integer, default=None)

    # 최고 시장 가치
    peak_market_value: Mapped[int | None] = mapped_column(Integer, default=None)

    # 시장 가치 변동률
    market_value_change_percentage: Mapped[float | None] = mapped_column(
        Float, default=None
    )

    # 이적료 이력
    transfer_fee_history: Mapped[list[dict] | None] = mapped_column(JSON, default=None)

    # 시즌별 통계
    season_statistics: Mapped[list[dict] | None] = mapped_column(JSON, default=None)

    # 커리어 통계
    career_statistics: Mapped[dict | None] = mapped_column(JSON, default=None)

    # 이적 이력
    transfer_history: Mapped[list[dict] | None] = mapped_column(JSON, default=None)

    # SNS 팔로워
    social_media_followers: Mapped[dict | None] = mapped_column(JSON, default=None)

    # 뉴스 언급 횟수
    news_mentions_count: Mapped[int | None] = mapped_column(Integer, default=None)

    # 검색 트렌드 점수
    search_trend_score: Mapped[float | None] = mapped_column(Float, default=None)

    # 팬 평점
    fan_rating: Mapped[float | None] = mapped_column(Float, default=None)

    # 미디어 주목도
    media_attention_score: Mapped[float | None] = mapped_column(Float, default=None)

    # 계약 정보
    contract_status: Mapped[dict | None] = mapped_column(JSON, default=None)

    # 수상 기록
    awards: Mapped[list[dict] | None] = mapped_column(JSON, default=None)

    # 선수 관계
    player = relationship("PlayerModel", back_populates="details")

    # 팀 관계
    team = relationship("TeamModel", back_populates="details")

    # 경기 영향 지표 관계
    match_affect_features = relationship(
        "PlayerMatchAffectFeaturesModel",
        back_populates="details",
    )

