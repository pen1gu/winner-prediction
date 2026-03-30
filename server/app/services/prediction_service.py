from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.compute.player_rating import predict_match_outcomes
from server.app.repositories.prediction_repository import (
    fetch_match_for_prediction,
    load_players_for_prediction,
)
from server.app.schemas.prediction import MatchOutcomesRead


async def get_match_outcomes(
    session: AsyncSession,
    *,
    match_id: int,
) -> MatchOutcomesRead:
    match = await fetch_match_for_prediction(
        session,
        match_id=match_id,
    )

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

    home_players = await load_players_for_prediction(
        session,
        player_ids=home_detail.starting_players,
    )
    away_players = await load_players_for_prediction(
        session,
        player_ids=away_detail.starting_players,
    )

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
