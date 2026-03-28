from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlmodel import select

from server.app.compute.player_rating import predict_match_outcomes
from server.app.models import MatchInfos, MatchLogs, Player
from server.app.models.session import get_session

router = APIRouter(prefix="/predictions", tags=["Prediction"])


class MatchOutcomesRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    match_id: int = Field(description="경기 ID (match_logs.id)")
    home_team_name: str = Field(description="홈 팀 이름")
    away_team_name: str = Field(description="원정 팀 이름")
    home: float = Field(description="홈 승 확률 (0~1)")
    draw: float = Field(description="무승부 확률 (0~1)")
    away: float = Field(description="원정 승 확률 (0~1)")


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


@router.get(
    "/matches/{match_id}/outcomes",
    response_model=MatchOutcomesRead,
    status_code=status.HTTP_200_OK,
    summary="경기별 승·무·패 확률",
)
async def get_match_outcomes(
    match_id: int,
    session: AsyncSession = Depends(get_session),
) -> MatchOutcomesRead:
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

    home_players = await _get_players_by_ids(session, home_detail.starting_players)
    away_players = await _get_players_by_ids(session, away_detail.starting_players)

    if not home_players or not away_players:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="선발 라인업 선수 정보가 부족합니다.",
        )

    outcomes = await predict_match_outcomes(
        session,
        home_players,
        away_players,
        home_detail.team_id,
        away_detail.team_id,
    )

    return MatchOutcomesRead(
        match_id=match_id,
        home_team_name=home_name,
        away_team_name=away_name,
        home=outcomes["home"],
        draw=outcomes["draw"],
        away=outcomes["away"],
    )
