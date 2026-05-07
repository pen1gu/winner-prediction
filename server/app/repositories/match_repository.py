from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlmodel import select

from server.app.models import MatchInfos, MatchLogs


async def fetch_match_log_by_id_with_teams_and_details(
    session: AsyncSession,
    *,
    match_id: int,
) -> MatchLogs | None:
    """
    예측·시각화 공통: match_infos(홈/원정 팀), match_details eager load.
    """
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
        return result.scalars().first()
    finally:
        result.close()
