from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlmodel import select

from server.app.compute.player_rating import compute_player_rating
from server.app.models import MatchInfos, MatchLogs, MatchDetails, Player
from server.app.models.session import get_session

router = APIRouter(prefix="/visualization", tags=["Visualization"])


@dataclass(frozen=True)
class _MatchSides:
    match: MatchLogs
    home_detail: MatchDetails
    away_detail: MatchDetails
    home_team_name: str
    away_team_name: str


async def _get_players_by_ids(
    session: AsyncSession, player_ids: List[int]
) -> List[Player]:
    if not player_ids:
        return []
    statement = (
        select(Player)
        .where(Player.id.in_(player_ids))
        .options(
            joinedload(Player.info),
            joinedload(Player.match_affect_features),
            joinedload(Player.match_details),
        )
    )
    result = await session.execute(statement)
    return list(result.scalars().unique().all())


async def _load_match_sides(session: AsyncSession, match_id: int) -> _MatchSides:
    statement = (
        select(MatchLogs)
        .where(MatchLogs.id == match_id)
        .options(
            joinedload(MatchLogs.match_details),
            joinedload(MatchLogs.match_infos).joinedload(MatchInfos.home_team),
            joinedload(MatchLogs.match_infos).joinedload(MatchInfos.away_team),
        )
    )
    result = await session.execute(statement)
    match = result.scalars().first()

    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="경기를 찾을 수 없습니다.",
        )

    home_name = (
        match.match_infos.home_team.name
        if match.match_infos and match.match_infos.home_team
        else "Home"
    )
    away_name = (
        match.match_infos.away_team.name
        if match.match_infos and match.match_infos.away_team
        else "Away"
    )

    home_detail = next((d for d in match.match_details if d.is_home), None)
    away_detail = next((d for d in match.match_details if not d.is_home), None)

    if not home_detail or not away_detail:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="홈/어웨이 경기 상세 정보가 없습니다.",
        )

    return _MatchSides(
        match=match,
        home_detail=home_detail,
        away_detail=away_detail,
        home_team_name=home_name,
        away_team_name=away_name,
    )


class TeamMetricPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str = Field(description="차트 시리즈 식별자")
    label: str = Field(description="축·범례용 한글 라벨")
    home: Optional[float] = Field(default=None, description="홈 팀 값")
    away: Optional[float] = Field(default=None, description="원정 팀 값")


class TeamStatsComparisonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    match_id: int
    home_team_name: str
    away_team_name: str
    match_date: Optional[datetime] = Field(default=None, description="경기 일시(UTC)")
    league_name: Optional[str] = Field(default=None, description="리그명")
    metrics: List[TeamMetricPoint] = Field(description="홈/원정 비교용 수치 열")


def _num(v) -> Optional[float]:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _player_match_rating(pr_map: dict, player_id: int) -> Optional[float]:
    if not pr_map:
        return None
    return _num(pr_map.get(str(player_id)))


@router.get(
    "/matches/{match_id}/team-stats",
    response_model=TeamStatsComparisonRead,
    status_code=status.HTTP_200_OK,
    summary="팀 스탯 비교(막대·레이더 차트용)",
)
async def get_match_team_stats_for_charts(
    match_id: int,
    session: AsyncSession = Depends(get_session),
) -> TeamStatsComparisonRead:
    ctx = await _load_match_sides(session, match_id)
    h, a = ctx.home_detail, ctx.away_detail

    infos = ctx.match.match_infos
    match_date = infos.match_date if infos else None
    league_name = infos.league_name if infos else None

    metrics: List[TeamMetricPoint] = [
        TeamMetricPoint(
            key="score",
            label="득점",
            home=_num(h.score),
            away=_num(a.score),
        ),
        TeamMetricPoint(
            key="expected_goals",
            label="xG",
            home=_num(h.expected_goals_value),
            away=_num(a.expected_goals_value),
        ),
        TeamMetricPoint(
            key="possession",
            label="점유율(%)",
            home=_num(h.possession),
            away=_num(a.possession),
        ),
        TeamMetricPoint(
            key="shots_total",
            label="슈팅",
            home=_num(h.shots_total),
            away=_num(a.shots_total),
        ),
        TeamMetricPoint(
            key="shots_on_target",
            label="유효슈팅",
            home=_num(h.shots_on_target),
            away=_num(a.shots_on_target),
        ),
        TeamMetricPoint(
            key="corners",
            label="코너",
            home=_num(h.corners),
            away=_num(a.corners),
        ),
        TeamMetricPoint(
            key="big_chances",
            label="결정적 기회",
            home=_num(h.big_chances),
            away=_num(a.big_chances),
        ),
        TeamMetricPoint(
            key="team_rating",
            label="팀 평점",
            home=_num(h.team_rating),
            away=_num(a.team_rating),
        ),
    ]

    return TeamStatsComparisonRead(
        match_id=match_id,
        home_team_name=ctx.home_team_name,
        away_team_name=ctx.away_team_name,
        match_date=match_date,
        league_name=league_name,
        metrics=metrics,
    )


class LineupRatingPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    player_id: int
    name: str
    is_home: bool
    model_rating: float = Field(description="모델 기반 산출 레이팅")
    match_rating: Optional[float] = Field(
        default=None, description="경기 데이터에 포함된 선수 평점(있을 때)"
    )


class LineupRatingsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    match_id: int
    home_team_name: str
    away_team_name: str
    players: List[LineupRatingPoint] = Field(
        description="선발 기준, model_rating 내림차순"
    )


@router.get(
    "/matches/{match_id}/lineup-ratings",
    response_model=LineupRatingsRead,
    status_code=status.HTTP_200_OK,
    summary="선발 라인업 레이팅(막대·분포 차트용)",
)
async def get_match_lineup_ratings_for_charts(
    match_id: int,
    session: AsyncSession = Depends(get_session),
) -> LineupRatingsRead:
    ctx = await _load_match_sides(session, match_id)

    home_players = await _get_players_by_ids(
        session, ctx.home_detail.starting_players
    )
    away_players = await _get_players_by_ids(
        session, ctx.away_detail.starting_players
    )

    if not home_players or not away_players:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="선발 라인업 선수 정보가 부족합니다.",
        )

    points: List[LineupRatingPoint] = []

    for p in home_players:
        points.append(
            LineupRatingPoint(
                player_id=p.id,
                name=(p.info.name if p.info and p.info.name else str(p.id)),
                is_home=True,
                model_rating=await compute_player_rating(p),
                match_rating=_player_match_rating(
                    ctx.home_detail.player_ratings or {}, p.id
                ),
            )
        )

    for p in away_players:
        points.append(
            LineupRatingPoint(
                player_id=p.id,
                name=(p.info.name if p.info and p.info.name else str(p.id)),
                is_home=False,
                model_rating=await compute_player_rating(p),
                match_rating=_player_match_rating(
                    ctx.away_detail.player_ratings or {}, p.id
                ),
            )
        )

    points.sort(key=lambda x: x.model_rating, reverse=True)

    return LineupRatingsRead(
        match_id=match_id,
        home_team_name=ctx.home_team_name,
        away_team_name=ctx.away_team_name,
        players=points,
    )
