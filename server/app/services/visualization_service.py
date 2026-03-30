from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlmodel import select

from server.app.compute.player_rating import compute_player_rating
from server.app.models import MatchDetails, MatchInfos, MatchLogs, Player
from server.app.schemas.visualization import (
    LineupRatingPoint,
    LineupRatingsRead,
    TeamMetricPoint,
    TeamStatsComparisonRead,
)


@dataclass(frozen=True)
class _MatchSides:
    match: MatchLogs
    home_detail: MatchDetails
    away_detail: MatchDetails
    home_team_name: str
    away_team_name: str


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


async def _get_players_by_ids(
    session: AsyncSession, player_ids: list[int]
) -> list[Player]:
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
    try:
        return list(result.scalars().unique().all())
    finally:
        await result.close()


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
    try:
        match = result.scalars().first()
    finally:
        await result.close()

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


async def get_match_team_stats_for_charts(
    session: AsyncSession,
    *,
    match_id: int,
) -> TeamStatsComparisonRead:
    ctx = await _load_match_sides(session, match_id)
    h, a = ctx.home_detail, ctx.away_detail

    infos = ctx.match.match_infos
    match_date: datetime | None = infos.match_date if infos else None
    league_name: str | None = infos.league_name if infos else None

    metrics: list[TeamMetricPoint] = [
        TeamMetricPoint(key="score", label="득점", home=_num(h.score), away=_num(a.score)),
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


async def get_match_lineup_ratings_for_charts(
    session: AsyncSession,
    *,
    match_id: int,
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

    points: list[LineupRatingPoint] = []
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

