"""
임시 실행 스크립트: FotMob matchDetails를 Playwright + playwright-stealth로 조회.

Poetry: poetry run python crawling_task.py
(최초 1회) poetry run playwright install chromium

Turnstile 등으로 막히면 headless 비활성화(.env 또는 Settings) 또는 수동 과제 확인.

PRINT_CF_SESSION=True: session_app으로 수집한 쿠키·UA·storage_state만 JSON으로 출력하고 종료.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any, Dict

from playwright.async_api import async_playwright
from playwright_stealth import Stealth

from server.app.session_maker.session_app import CfBrowserSession, obtain_cf_browser_session
from server.config.settings import settings

MATCH_ID = 4771847
TEAM_ID = 9825

# True면 matchDetails 조회 없이 Cloudflare/브라우저 세션 스냅샷만 stdout에 JSON 출력
PRINT_CF_SESSION = True


def _match_details_url(match_id: int) -> str:
    base = settings.fotmob_api_url.rstrip("/")
    return f"{base}/data/matchDetails?matchId={match_id}"


async def fetch_match_details_via_stealth(match_id: int) -> Dict[str, Any]:
    url = _match_details_url(match_id)
    stealth = Stealth()

    async with stealth.use_async(async_playwright()) as p:
        browser = await p.chromium.launch(headless=settings.browser_headless)
        try:
            context = await browser.new_context(
                user_agent=settings.user_agent,
                locale=f"{settings.fotmob_language}-KR",
                viewport={"width": 1365, "height": 900},
                extra_http_headers={
                    "Accept-Language": f"{settings.fotmob_language}-KR,{settings.fotmob_language};q=0.9,en-US;q=0.8,en;q=0.7",
                },
            )
            page = await context.new_page()

            maybe_home = settings.fotmob_base_url.rstrip("/") + "/"
            await page.goto(maybe_home, wait_until="domcontentloaded", timeout=settings.browser_timeout)

            response = await page.goto(url, wait_until="domcontentloaded", timeout=settings.browser_timeout)
            if response is None:
                raise RuntimeError("matchDetails 네비게이션 응답 없음")

            if response.status != 200:
                body_preview = (await response.text())[:800]
                raise RuntimeError(
                    f"matchDetails HTTP {response.status}: {body_preview}"
                )

            return await response.json()
        finally:
            await browser.close()


def _session_snapshot_for_print(session: CfBrowserSession) -> Dict[str, Any]:
    return {
        "user_agent": session.user_agent,
        "cookies": session.cookies,
        "storage_state": session.storage_state,
    }


async def print_cf_session_snapshot() -> None:
    session = await obtain_cf_browser_session(headless=settings.browser_headless)
    print(json.dumps(_session_snapshot_for_print(session), ensure_ascii=False, indent=2, default=str))


async def main() -> None:
    await print_cf_session_snapshot()

    # data = await fetch_match_details_via_stealth(MATCH_ID)
    # general = data.get("general") or {}
    # home = (general.get("homeTeam") or {}).get("name")
    # away = (general.get("awayTeam") or {}).get("name")
    # mid = general.get("matchId")
    # print(f"matchId={mid} {home} vs {away}")

    # from server.app.tasks.task import fetch_team_overview_task, fetch_matches_by_team_id_task, compute_all_player_ratings_task
    # await fetch_team_overview_task(TEAM_ID)
    # await fetch_matches_by_team_id_task(TEAM_ID)
    # await compute_all_player_ratings_task()


if __name__ == "__main__":
    asyncio.run(main())
