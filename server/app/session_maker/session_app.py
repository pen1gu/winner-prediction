"""
Playwright(+stealth)로 브라우저 컨텍스트를 연 뒤 Cloudflare 계열 쿠키와 UA를 수집한다.

Turnstile/JS 챌린지는 환경에 따라 headless=False·수동 완료가 필요할 수 있다.
모듈 import 시 네트워크·브라우저를 열지 않는다.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Literal, Sequence

import httpx
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

from server.config.settings import settings
from server.utils.logger import get_logger

logger = get_logger(__name__)

# Cloudflare 대기 루프 폴링 간격(초)
_COOKIE_POLL_INTERVAL_S = 0.35

# max_wait_ms 기본: API 타임아웃보다 챌린지 해결에 여유를 둔다
_DEFAULT_CF_WAIT_MS = max(120_000, int(settings.browser_timeout * 4))


@dataclass(frozen=True)
class CfBrowserSession:
    """브라우저에서 수집한 쿠키·UA·storage_state."""

    cookies: list[dict[str, Any]]
    user_agent: str
    storage_state: dict[str, Any]


async def obtain_cf_browser_session(
    *,
    target_url: str | None = None,
    required_cookie_names: Sequence[str] = ("cf_clearance", "__cf_bm"),
    max_wait_ms: int | None = None,
    post_ready_sleep_ms: int = 0,
    headless: bool | None = None,
    wait_until: Literal["commit", "domcontentloaded", "load", "networkidle"] = "domcontentloaded",
) -> CfBrowserSession:
    """
    대상 URL까지 이동한 뒤 지정 쿠키가 생길 때까지 폴링하고 세션 스냅샷을 반환한다.

    Args:
        target_url: 방문할 URL. None이면 FotMob 홈(settings.fotmob_base_url/)과 동일 규칙.
        required_cookie_names: 모두 존재할 때까지 대기. 빈 시퀀스면 goto 직후 바로 수집.
        max_wait_ms: 폴링 최대 시간(ms). None이면 프로젝트 기본 긴 대기값 사용.
        post_ready_sleep_ms: 조건 충족 후 추가 안정화 대기(ms).
        headless: None이면 settings.browser_headless 사용.
        wait_until: page.goto wait_until (networkidle은 느리거나 멈출 수 있음).

    Returns:
        쿠키 목록(Playwright 형식), 실제 navigator.userAgent, context.storage_state().

    Raises:
        RuntimeError: 타임아웃 시. headless 해제·수동 과제 완료를 권장한다.
    """
    url = target_url if target_url is not None else settings.fotmob_base_url.rstrip("/") + "/"
    deadline_s = time.monotonic() + (max_wait_ms if max_wait_ms is not None else _DEFAULT_CF_WAIT_MS) / 1000.0
    use_headless = settings.browser_headless if headless is None else headless
    required: set[str] = set(required_cookie_names)

    stealth = Stealth()
    async with stealth.use_async(async_playwright()) as p:
        browser = await p.chromium.launch(headless=use_headless)
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
            timeout_ms = int((deadline_s - time.monotonic()) * 1000)
            if timeout_ms < 1000:
                timeout_ms = 1000
            await page.goto(url, wait_until=wait_until, timeout=timeout_ms)

            if required:
                logger.info(
                    "Cloudflare 세션 대기 시작 url=%s required=%s headless=%s",
                    url,
                    sorted(required),
                    use_headless,
                )
                while True:
                    cookies_now = await context.cookies()
                    present = {c.get("name") for c in cookies_now if c.get("name")}
                    if required <= present:
                        logger.info("필요 쿠키 수신 완료: %s", sorted(required & present))
                        break
                    if time.monotonic() >= deadline_s:
                        still_missing = required - present
                        raise RuntimeError(
                            "Cloudflare/챌린지 쿠키 대기 타임아웃 "
                            f"(누락: {sorted(still_missing)}). "
                            ".env에서 browser_headless=false 또는 수동으로 과제를 완료해 보세요."
                        )
                    await asyncio.sleep(_COOKIE_POLL_INTERVAL_S)

            if post_ready_sleep_ms > 0:
                await page.wait_for_timeout(post_ready_sleep_ms)

            cookies = await context.cookies()
            ua = await page.evaluate("navigator.userAgent")
            storage_state = await context.storage_state()
            return CfBrowserSession(cookies=cookies, user_agent=str(ua), storage_state=storage_state)
        finally:
            await browser.close()


def playwright_cookies_to_httpx_cookies(
    playwright_cookies: list[dict[str, Any]],
) -> httpx.Cookies:
    """Playwright context.cookies() 결과를 httpx.Cookies로 옮긴다."""
    jar = httpx.Cookies()
    for c in playwright_cookies:
        name = c.get("name")
        if not name:
            continue
        value = c.get("value")
        if value is None:
            continue
        jar.set(
            name,
            value,
            domain=c.get("domain") or "",
            path=c.get("path") or "/",
        )
    return jar
