from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional
from datetime import datetime

from server.app.models.player import Player
from server.app.models.team import Team
from server.utils.model.pydantic_model import Model

"""
description: 변경될 가능성이 높은 선수 경력 상세 정보
"""

class PlayerDetails(Model):
    model_config = ConfigDict(from_attributes=True)
    player: Player = Field(default=Player())

    team: Team = Field(default=Team())

    # 시장 가치 변동 이력 (날짜, 가치, 변동률 포함)
    market_value_history: Optional[List[Dict]] = Field(default=None)

    # 현재 시장 가치
    current_market_value: Optional[int] = Field(default=None)

    # 최고 시장 가치
    peak_market_value: Optional[int] = Field(default=None)

    # 최근 시장 가치 변동률 (퍼센트)
    market_value_change_percentage: Optional[float] = Field(default=None)

    # 이적료 이력
    transfer_fee_history: Optional[List[Dict]] = Field(default=None)

    # 시즌별 통계 (골, 어시스트, 경기 수 등)
    season_statistics: Optional[List[Dict]] = Field(default=None)

    # 통산 통계
    career_statistics: Optional[Dict] = Field(default=None)

    # 이적 이력
    transfer_history: Optional[List[Dict]] = Field(default=None)

    # SNS 팔로워 수 (인스타, 트위터 등)
    social_media_followers: Optional[Dict] = Field(default=None)

    # 최근 언급 횟수
    news_mentions_count: Optional[int] = Field(default=None)

    # 검색 트렌드 점수
    search_trend_score: Optional[float] = Field(default=None)

    # 팬 평가 점수
    fan_rating: Optional[float] = Field(default=None)

    # 미디어 주목도 점수
    media_attention_score: Optional[float] = Field(default=None)

    # 계약 상태 (만료일, 연봉 등)
    contract_status: Optional[Dict] = Field(default=None)

    # 수상 이력
    awards: Optional[List[Dict]] = Field(default=None)