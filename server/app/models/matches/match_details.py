from typing import Optional, TYPE_CHECKING, List, Dict
from sqlmodel import Relationship, SQLModel, Field, JSON, Column

from server.utils.model.db_model import TimestampMixin

if TYPE_CHECKING:
    from server.app.models.matches.match_logs import MatchLogs

class MatchDetailsBase(SQLModel):
    """MatchDetails 기본 정보 (공통 필드)"""

    # 경기 기본 정보
    match_name: Optional[str] = Field(default=None)

    league_name: Optional[str] = Field(default=None)

    match_round: Optional[str] = Field(default=None)

    match_time_utc: Optional[str] = Field(default=None)

    started: Optional[bool] = Field(default=None)

    finished: Optional[bool] = Field(default=None)

    # 경기장 및 심판 정보
    stadium: Optional[str] = Field(default=None)

    referee: Optional[str] = Field(default=None)

    # 상세 스코어 및 진행 정보
    score_str: Optional[str] = Field(default=None)

    halfs_info: Optional[Dict] = Field(default=None, sa_column=Column(JSON))

    # 승부차기 결과
    penalty_shootout_reason: Optional[str] = Field(default=None)

    penalties: Optional[List[int]] = Field(default=None, sa_column=Column(JSON))

    who_lost_on_penalties: Optional[str] = Field(default=None)

    # 관중 수
    attendance: Optional[int] = Field(default=None)

    # 득점 및 주요 이벤트
    events: Optional[List[Dict]] = Field(default=None, sa_column=Column(JSON))

    # 팀 xG
    home_expected_goals: Optional[float] = Field(default=None)

    away_expected_goals: Optional[float] = Field(default=None)

    # 팀 상세 스탯 (슈팅, 점유율 등)
    home_stats: Optional[Dict] = Field(default=None, sa_column=Column(JSON))

    away_stats: Optional[Dict] = Field(default=None, sa_column=Column(JSON))

    # MOM (Man of the Match)
    player_of_the_match: Optional[Dict] = Field(default=None, sa_column=Column(JSON))

    # 슈팅맵 및 전술 흐름
    shotmap: Optional[Dict] = Field(default=None, sa_column=Column(JSON))

    # 홈 팀 선수 목록
    home_starting_players: Optional[List[Dict]] = Field(default=None, sa_column=Column(JSON))

    home_substitute_players: Optional[List[Dict]] = Field(default=None, sa_column=Column(JSON))

    home_lineup_power_rating: Optional[float] = Field(default=None)

    # 어웨이 팀 선수 목록
    away_starting_players: Optional[List[Dict]] = Field(default=None, sa_column=Column(JSON))

    away_substitute_players: Optional[List[Dict]] = Field(default=None, sa_column=Column(JSON))

    away_lineup_power_rating: Optional[float] = Field(default=None)

class MatchDetails(MatchDetailsBase, TimestampMixin, table=True):
    __tablename__ = "match_details"
    
    # match_logs.id를 PK이자 FK로 사용 (1:1 매칭)
    id: int = Field(primary_key=True, foreign_key="match_logs.id")

    match_logs: "MatchLogs" = Relationship(
        back_populates="match_details",
        sa_relationship_kwargs={"lazy": "select"}
    )
