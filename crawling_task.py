import asyncio
from playwright.async_api import async_playwright

from server.app.tasks.task import (
    fetch_team_overview_task,
    fetch_matches_by_team_id_task,
    compute_all_player_ratings_task,
)


TEAM_ID = 9825

FOTMOB_TEAM_OVERVIEW_URL = "https://www.fotmob.com/ko/teams/9825/overview/arsenal"

FOTMOB_DESKTOP_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/145.0.0.0 Safari/537.36"
)

FOTMOB_EXTRA_HTTP_HEADERS = {
    "sec-ch-ua": '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "Referer": FOTMOB_TEAM_OVERVIEW_URL,
    "x-mas": (
        "eyJib2R5Ijp7InVybCI6Ii9hcGkvZGF0YS9tYXRjaD9pZD01MjMxMDQ1IiwiY29kZSI6MTc3NTI2MzUwMzYyMCwiZm9vIjoicHJvZHVjdGlvbjo3NGFjMmVkYWE3ZDQyNTMwZmE0OTMzMGVmZTFlZWRjZmIyMWI1NTVkIn0sInNpZ25hdHVyZSI6IjgyMDU2ODg5ODkyRkY5MTc1MkRFRjc0MDFBNzE2QUU5In0="
    ),
}


async def main() -> None:

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent=FOTMOB_DESKTOP_UA,
            extra_http_headers=FOTMOB_EXTRA_HTTP_HEADERS,
        )
        page = await context.new_page()
        await page.goto(
            FOTMOB_TEAM_OVERVIEW_URL,
            wait_until="networkidle",
        )
        await asyncio.sleep(120)  # 챌린지 완료 대기
        cookies = await context.cookies()
        cf_clearance = next((c["value"] for c in cookies if c["name"] == "cf_clearance"), None)
        print(cf_clearance)  # 출력: 토큰 값
        await browser.close()

    # await fetch_team_overview_task(TEAM_ID)

    # await fetch_matches_by_team_id_task(TEAM_ID)

    # await compute_all_player_ratings_task()

if __name__ == "__main__":
    asyncio.run(main())

