from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime

from server.app.model.player import Player
from server.app.model.team import Team


class PlayerDetails(BaseModel):
    player: Player = Field(default=Player())

    team: Team = Field(default=Team())

    years_of_market_values: List[int] = Field(default=[])

    # 시장 가치 변동 이력 (날짜, 가치, 변동률 포함)
    market_value_history: List[Dict] = Field(default=[])

    # 현재 시장 가치
    current_market_value: int = Field(default=0)

    # 최고 시장 가치
    peak_market_value: int = Field(default=0)

    # 최근 시장 가치 변동률 (퍼센트)
    market_value_change_percentage: float = Field(default=0.0)

    # 이적료 이력
    transfer_fee_history: List[Dict] = Field(default=[])

    # 시즌별 통계 (골, 어시스트, 경기 수 등)
    season_statistics: List[Dict] = Field(default=[])

    # 통산 통계
    career_statistics: Dict = Field(default={})

    # 성적 추이 (최근 N경기)
    performance_trend: List[Dict] = Field(default=[])

    # 부상 이력
    injury_history: List[Dict] = Field(default=[])

    # 이적 이력
    transfer_history: List[Dict] = Field(default=[])

    # SNS 팔로워 수 (인스타, 트위터 등)
    social_media_followers: Dict = Field(default={})

    # 최근 언급 횟수
    news_mentions_count: int = Field(default=0)

    # 검색 트렌드 점수
    search_trend_score: float = Field(default=0.0)

    # 팬 평가 점수
    fan_rating: float = Field(default=0.0)

    # 미디어 주목도 점수
    media_attention_score: float = Field(default=0.0)

    # 현재 폼 (Excellent, Good, Average, Poor)
    current_form: str = Field(default="")

    # 폼 점수 (0-10)
    form_rating: float = Field(default=0.0)

    # 최근 경기 기록
    recent_matches: List[Dict] = Field(default=[])

    # 계약 상태 (만료일, 연봉 등)
    contract_status: Dict = Field(default={})

    # 출전 가능 여부
    availability_status: str = Field(default="")

    # 수상 이력
    awards: List[Dict] = Field(default=[])

    # 국가대표 출전 횟수
    national_team_caps: int = Field(default=0)

    # 출전 시간 통계
    playing_time_stats: Dict = Field(default={})

    # 동료 선수 대비 통계
    comparison_with_peers: Dict = Field(default={})