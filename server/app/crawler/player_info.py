import httpx
import json
import asyncio
from playwright.async_api import async_playwright

from server.app.model.player_details import PlayerDetails
from server.config.settings import settings
from server.utils.http.requests import FotMobHTTPClient

class PlayerInfoCrawler:
    def __init__(self):
        self.browser = None
        self.page = None
        self.playwright = None
        # asyncio.run(self.initialize_browser())

    async def initialize_browser(self):
        """비동기 초기화"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=settings.browser_headless)
        self.page = await self.browser.new_page()
        await self.page.goto(f"{settings.fotmob_base_url}/{settings.fotmob_language}")

    async def get_players_info(self, team_id: int) -> PlayerDetails:
        """선수 정보 조회"""
        if self.page is None:
            await self.initialize_browser()
        await self.page.goto(f"https://www.fotmob.com/{settings.fotmob_language}/team/{team_id}")
        content = await self.page.content()
        return PlayerDetails.model_validate_json(content)

    async def close(self):
        """리소스 정리"""
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
        self.page = None

    def __del__(self):
        """소멸자에서 리소스 정리 (동기)"""
        # 소멸자에서는 async 작업을 안전하게 수행할 수 없으므로
        # 명시적으로 close()를 호출하도록 권장
        pass

    async def __aenter__(self):
        """Context manager 진입"""
        if self.page is None:
            await self.initialize_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager 종료"""
        await self.close()


    async def test_httpx(self):
        """HTTP 클라이언트 테스트"""
        client = FotMobHTTPClient()
        response = await client.get(
            "/data/teams",
            params={"id": 9825, "ccode3": "KOR"}
        )
        print(response.text)




player_info = PlayerInfoCrawler()