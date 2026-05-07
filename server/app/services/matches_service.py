from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from server.app.api.prediction.lineup import try_predict_match_outcomes
from server.app.mappers.match_mapper import match_log_to_summary_dict
from server.app.schemas.matches import LatestMatchesRead, MatchSummaryRead
from server.app.store.db_query import (
    fetch_recent_match_logs_for_list,
    fetch_recent_match_summaries,
)


async def get_latest_matches(
    session: AsyncSession,
    *,
    limit: int,
    include_outcomes: bool,
) -> LatestMatchesRead:
    if include_outcomes:
        logs = await fetch_recent_match_logs_for_list(session, limit=limit)
        summaries: list[MatchSummaryRead] = []
        for m in logs:
            row = match_log_to_summary_dict(m)
            probs = await try_predict_match_outcomes(session, m)
            row["outcomes"] = (
                {"home": probs["home"], "draw": probs["draw"], "away": probs["away"]}
                if probs
                else None
            )
            summaries.append(MatchSummaryRead.model_validate(row))
    else:
        rows = await fetch_recent_match_summaries(session, limit=limit)
        summaries = [MatchSummaryRead.model_validate(row) for row in rows]

    return LatestMatchesRead(ok=True, count=len(summaries), matches=summaries)

