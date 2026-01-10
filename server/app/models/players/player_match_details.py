from typing import Optional, List, Dict, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from sqlalchemy import ForeignKey, Integer, ForeignKeyConstraint

from server.utils.model.db_model import TimestampMixin

if TYPE_CHECKING:
    from .player import Player
    from server.app.models.teams.team import Team
    from server.app.models.matches.match_logs import MatchLogs
    from server.app.models.matches.match_details import MatchDetails

class PlayerMatchDetailsBase(SQLModel):
    """경기별 선수 성과 상세 정보 기본"""
    
    # 포지션 (경기에서 뛴 포지션)
    position: Optional[str] = Field(default=None, max_length=32)
    
    # 출전 시간 (분)
    minutes_played: Optional[int] = Field(default=None)
    
    # 선발 출전 여부
    is_starter: bool = Field(default=False)
    
    # 교체 인/아웃 시간 (분)
    substitution_in_minute: Optional[int] = Field(default=None)
    substitution_out_minute: Optional[int] = Field(default=None)
    
    # 평점 (FotMob rating)
    rating: Optional[float] = Field(default=None)
    
    # Man of the Match 여부
    is_man_of_the_match: bool = Field(default=False)
    
    # --- 공격 스탯 ---
    # 골
    goals: int = Field(default=0)
    
    # 어시스트
    assists: int = Field(default=0)
    
    # 전체 슈팅 수
    shots_total: Optional[int] = Field(default=None)
    
    # 유효 슈팅 수
    shots_on_target: Optional[int] = Field(default=None)
    
    # 기대 득점 (xG)
    expected_goals: Optional[float] = Field(default=None)
    
    # 기대 득점 유효슈팅 기준 (xGOT)
    expected_goals_on_target: Optional[float] = Field(default=None)
    
    # 기대 어시스트 (xA)
    expected_assists: Optional[float] = Field(default=None)
    
    # xG + xA
    expected_goals_plus_assists: Optional[float] = Field(default=None)
    
    # --- 패스 스탯 ---
    # 패스 성공 수
    passes_completed: Optional[int] = Field(default=None)
    
    # 패스 시도 수
    passes_attempted: Optional[int] = Field(default=None)
    
    # 패스 성공률 (%)
    pass_accuracy: Optional[float] = Field(default=None)
    
    # 파이널 서드 패스 성공 수
    final_third_passes: Optional[int] = Field(default=None)
    
    # 롱패스 성공 수
    long_passes_completed: Optional[int] = Field(default=None)
    
    # 크로스 성공 수
    crosses_completed: Optional[int] = Field(default=None)
    
    # --- 수비 스탯 ---
    # 태클
    tackles: Optional[int] = Field(default=None)
    
    # 인터셉트
    interceptions: Optional[int] = Field(default=None)
    
    # 클리어링
    clearances: Optional[int] = Field(default=None)
    
    # 리커버리
    recoveries: Optional[int] = Field(default=None)
    
    # 블록
    blocks: Optional[int] = Field(default=None)
    
    # 드리블 저지
    dribbles_stopped: Optional[int] = Field(default=None)
    
    # --- 듀얼 스탯 ---
    # 지상 듀얼 승
    ground_duels_won: Optional[int] = Field(default=None)
    
    # 지상 듀얼 전체
    ground_duels_total: Optional[int] = Field(default=None)
    
    # 지상 듀얼 승률 (%)
    ground_duels_win_rate: Optional[float] = Field(default=None)
    
    # 공중 듀얼 승
    aerial_duels_won: Optional[int] = Field(default=None)
    
    # 공중 듀얼 전체
    aerial_duels_total: Optional[int] = Field(default=None)
    
    # 공중 듀얼 승률 (%)
    aerial_duels_win_rate: Optional[float] = Field(default=None)
    
    # --- 이벤트 로그 ---
    # 슈팅 이벤트 리스트 (JSON)
    shot_events: Optional[List[Dict]] = Field(default=None, sa_column=Column(JSON))
    
    # 카드 이벤트 (옐로우/레드)
    yellow_cards: int = Field(default=0)
    red_cards: int = Field(default=0)
    
    # 파울
    fouls: Optional[int] = Field(default=None)
    
    # 부상 이벤트
    injury_event: Optional[Dict] = Field(default=None, sa_column=Column(JSON))
    
    # --- 컨텍스트 정보 ---
    # 시즌 누적 골 (해당 시즌)
    season_goals: Optional[int] = Field(default=None)
    
    # 시즌 누적 어시스트 (해당 시즌)
    season_assists: Optional[int] = Field(default=None)
    
    # 시즌 평균 평점 (해당 시즌)
    season_average_rating: Optional[float] = Field(default=None)
    
    # 팀 내 top player 여부
    is_team_top_player: bool = Field(default=False)


class PlayerMatchDetails(PlayerMatchDetailsBase, TimestampMixin, table=True):
    """경기별 선수 성과 상세 정보 - SQLModel (DB + API)"""
    __tablename__ = "player_match_details"
    
    # 경기 FK (match_logs.id 참조) - 복합 PK의 일부
    match_id: int = Field(sa_column=Column(Integer, ForeignKey("match_logs.id", ondelete="CASCADE"), primary_key=True))
    
    # 선수 FK (players.id 참조) - 복합 PK의 일부이자 주 식별자
    id: int = Field(sa_column=Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), primary_key=True))
    
    # 팀 FK (teams.id 참조)
    team_id: int = Field(sa_column=Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False))
    
    # 복합 제약 조건 설정
    __table_args__ = (
        ForeignKeyConstraint(
            ["match_id", "team_id"],
            ["match_details.id", "match_details.team_id"],
            ondelete="CASCADE",
            name="fk_player_match_details_match_details"
        ),
    )
    
    # Relationships
    match: "MatchLogs" = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "PlayerMatchDetails.match_id==MatchLogs.id",
            "lazy": "select",
            "viewonly": True
        }
    )

    match_detail: "MatchDetails" = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "and_(PlayerMatchDetails.match_id==MatchDetails.id, PlayerMatchDetails.team_id==MatchDetails.team_id)",
            "lazy": "select",
            "viewonly": True
        }
    )
    
    player: "Player" = Relationship(
        back_populates="match_details",
        sa_relationship_kwargs={"lazy": "select"}
    )
    
    team: "Team" = Relationship(
        sa_relationship_kwargs={
            "lazy": "select",
            "overlaps": "player_match_details"
        }
    )
