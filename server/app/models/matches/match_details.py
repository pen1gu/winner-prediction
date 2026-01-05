from sqlalchemy.orm import foreign
from typing import Optional, TYPE_CHECKING, List, Dict
from sqlmodel import Relationship, SQLModel, Field, JSON, Column
from sqlalchemy import ForeignKey, Integer

from server.utils.model.db_model import TimestampMixin

if TYPE_CHECKING:
    from server.app.models.matches.match_logs import MatchLogs
    from server.app.models.teams.team import Team
    from server.app.models.players.player import Player

class MatchDetailsBase(SQLModel):
    """MatchDetails 팀별 상세 정보"""

    # 홈팀 여부 (True: 홈, False: 어웨이)
    is_home: bool = Field(default=True)

    # --- 경기 결과 (팀별) ---
    # 해당 팀의 득점
    score: int = Field(default=0)

    # 승부차기 득점 (있을 경우)
    penalty_score: Optional[int] = Field(default=None)

    # 승부차기 패배 여부
    is_penalty_loser: bool = Field(default=False)

    # 최종 스코어 문자열 (예: "2 - 3")
    score_str: Optional[str] = Field(default=None)

    # 승부차기 결과 요약 (예: "Pen 6 - 5")
    penalty_shootout_reason: Optional[str] = Field(default=None)

    # 기대 득점 (xG) 수치
    expected_goals_value: Optional[float] = Field(default=None)

    # 볼 점유율 (%)
    possession: Optional[float] = Field(default=None)

    # 전체 슈팅 수
    shots_total: Optional[int] = Field(default=None)

    # 유효 슈팅 수
    shots_on_target: Optional[int] = Field(default=None)

    # 결정적 기회 (Big Chances)
    big_chances: Optional[int] = Field(default=None)

    # 결정적 기회 미스
    big_chances_missed: Optional[int] = Field(default=None)

    # 코너킥
    corners: Optional[int] = Field(default=None)

    # 파울
    fouls: Optional[int] = Field(default=None)

    # 경고 (Yellow Cards)
    yellow_cards: Optional[int] = Field(default=None)

    # 퇴장 (Red Cards)
    red_cards: Optional[int] = Field(default=None)

    # 패스 성공 수
    accurate_passes: Optional[int] = Field(default=None)

    # 전체 패스 수
    total_passes: Optional[int] = Field(default=None)

    # 오프사이드
    offsides: Optional[int] = Field(default=None)

    # --- 선수 명단 및 레이팅 (ID 기반) ---
    # 선발 선수 ID 리스트
    starting_players: List[int] = Field(default_factory=list, sa_column=Column(JSON))

    # 교체 선수 ID 리스트
    substitute_players: List[int] = Field(default_factory=list, sa_column=Column(JSON))

    # 선수별 평점 매핑 (예: {"12345": 8.5})
    player_ratings: Dict[str, float] = Field(default_factory=dict, sa_column=Column(JSON))

    # 라인업 기반 전력 레이팅 (선수들의 개별 레이팅 가중 평균)
    lineup_power_rating: Optional[float] = Field(default=None)

class MatchDetails(MatchDetailsBase, TimestampMixin, table=True):
    __tablename__ = "match_details"
    
    # 복합 PK 및 FK 설정 - sa_column 방식으로 통일
    id: int = Field(sa_column=Column(Integer, ForeignKey("match_logs.id", ondelete="CASCADE"), primary_key=True))
    
    team_id: int = Field(sa_column=Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True))

    # MOM(Man of the Match) 선수 ID - sa_column 방식으로 통일
    potm_player_id: Optional[int] = Field(default=None, sa_column=Column(Integer, ForeignKey("players.id", ondelete="SET NULL"), nullable=True))

    # Relationships
    match_logs: "MatchLogs" = Relationship(
        back_populates="match_details",
        sa_relationship_kwargs={"lazy": "select"}
    )
    
    team: "Team" = Relationship(
        back_populates="match_details",
        sa_relationship_kwargs={"lazy": "select"}
    )

    potm_player: Optional["Player"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "MatchDetails.potm_player_id==foreign(Player.id)",
            "lazy": "select"
        }
    )
