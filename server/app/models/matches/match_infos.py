import datetime
from typing import Optional, TYPE_CHECKING, List, Dict
from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from sqlalchemy import ForeignKey, Integer, DateTime
from sqlalchemy.orm import foreign

from server.utils.model.db_model import TimestampMixin

if TYPE_CHECKING:
    from server.app.models.teams.team import Team
    from .match_logs import MatchLogs
    from .match_details import MatchDetails

class MatchInfosBase(SQLModel):
    """MatchInfos 경기 마스터 정보 (점수 제외 공통 메타데이터)"""
    
    # 경기 일시 (타임존 포함)
    match_date: datetime.datetime = Field(sa_type=DateTime(timezone=True), nullable=False)

    # 경기 명칭 (예: Milan vs Arsenal)
    match_name: Optional[str] = Field(default=None)

    # 리그 정보
    league_name: Optional[str] = Field(default=None)
    match_round: Optional[str] = Field(default=None)
    match_time_utc: Optional[str] = Field(default=None)

    # 장소 및 인원
    stadium: Optional[str] = Field(default=None)
    referee: Optional[str] = Field(default=None)
    attendance: Optional[int] = Field(default=None)
    
    # 날씨 정보 (기온, 습도, 상태 등)
    weather: Optional[Dict] = Field(default=None, sa_column=Column(JSON))

    # 경기 상태
    next_match: bool = Field(default=False)
    finished: bool = Field(default=False)
    cancelled: bool = Field(default=False)

    # 경기 진행 관련 복합 데이터 (점수와 직접 관련 없는 데이터들)
    # 전/후반 시작 및 종료 시간 정보
    halfs_info: Optional[Dict] = Field(default=None, sa_column=Column(JSON))

    # 경기 중 발생한 주요 이벤트 리스트 (교체, 카드 등 - 골은 결과이기도 하지만 흐름 파악을 위해 포함)
    events: Optional[List[Dict]] = Field(default=None, sa_column=Column(JSON))

    # 슈팅 데이터 및 위치 정보 (슈팅맵)
    shotmap: Optional[Dict] = Field(default=None, sa_column=Column(JSON))

class MatchInfos(MatchInfosBase, TimestampMixin, table=True):
    __tablename__ = "match_infos"

    id: int = Field(sa_column=Column(Integer, ForeignKey("match_logs.id", ondelete="CASCADE"), primary_key=True))
    
    home_team_id: int = Field(foreign_key="teams.id")
    away_team_id: int = Field(foreign_key="teams.id")

    # Relationships
    match_logs: "MatchLogs" = Relationship(back_populates="match_infos")
    
    home_team: "Team" = Relationship(sa_relationship_kwargs={"primaryjoin": "MatchInfos.home_team_id==Team.id"})
    away_team: "Team" = Relationship(sa_relationship_kwargs={"primaryjoin": "MatchInfos.away_team_id==Team.id"})

    # 이 경기의 팀별 상세 정보 (홈/어웨이)
    match_details: List["MatchDetails"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "MatchInfos.id==foreign(MatchDetails.id)",
            "lazy": "select",
            "viewonly": True
        }
    )
