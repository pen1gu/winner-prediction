import httpx
from typing import Dict, Optional, Any
from urllib.parse import urlencode

from server.config.settings import settings


class FotMobHTTPClient:
    """FotMob API용 HTTP 클라이언트"""
    
    def __init__(self, timeout: Optional[float] = None):
        """
        Args:
            timeout: HTTP 요청 타임아웃 (초). None이면 settings에서 가져옴
        """
        self.timeout = timeout or settings.http_timeout
        self.base_url = settings.fotmob_api_url
        self._default_headers = self._build_default_headers()
    
    def _build_default_headers(self) -> Dict[str, str]:
        """기본 헤더 생성"""
        return {
            "User-Agent": settings.user_agent,
            "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": f"{settings.fotmob_language}-KR,{settings.fotmob_language};q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": f"{settings.fotmob_base_url}/",
            "x-mas": "eyJib2R5Ijp7InVybCI6Ii9hcGkvZGF0YS90ZWFtcz9pZD05ODI1JmNjb2RlMz1LT1IiLCJjb2RlIjoxNzY0MjA5MzE4NTg3LCJmb28iOiJwcm9kdWN0aW9uOjEzMjc0NzhiNTQwNjc3NTIzNjhlOWUwZGEzZWUzNjM5MGJjMGY3NzcifSwic2lnbmF0dXJlIjoiQjc4N0I0RTdFRkEwN0QyMkYzQzFGNkNCNTczNURFMDAifQ==",
        }
    
    def _merge_headers(self, custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """기본 헤더와 커스텀 헤더 병합"""
        headers = self._default_headers.copy()
        if custom_headers:
            headers.update(custom_headers)
        return headers
    
    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        raise_for_status: bool = True,
        **kwargs
    ) -> httpx.Response:
        """
        GET 요청
        
        Args:
            url: 요청 URL (상대 경로 또는 전체 URL)
            params: 쿼리 파라미터
            headers: 추가/오버라이드할 헤더
            raise_for_status: HTTP 에러 시 예외 발생 여부 (기본값: True)
            **kwargs: httpx.AsyncClient.get()에 전달할 추가 인자
            
        Returns:
            httpx.Response 객체
        """
        # URL이 상대 경로인 경우 base_url 추가
        if not url.startswith("http"):
            url = f"{self.base_url}{url}" if url.startswith("/") else f"{self.base_url}/{url}"
        
        merged_headers = self._merge_headers(headers)
        
        client = httpx.AsyncClient(timeout=self.timeout)
        try:
            response = await client.get(
                url,
                params=params,
                headers=merged_headers,
                **kwargs
            )
            if raise_for_status:
                response.raise_for_status()
            return response
        finally:
            await client.aclose()
    
    async def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> httpx.Response:
        """
        POST 요청
        
        Args:
            url: 요청 URL (상대 경로 또는 전체 URL)
            data: 폼 데이터
            json: JSON 데이터
            params: 쿼리 파라미터
            headers: 추가/오버라이드할 헤더
            **kwargs: httpx.AsyncClient.post()에 전달할 추가 인자
            
        Returns:
            httpx.Response 객체
        """
        # URL이 상대 경로인 경우 base_url 추가
        if not url.startswith("http"):
            url = f"{self.base_url}{url}" if url.startswith("/") else f"{self.base_url}/{url}"
        
        merged_headers = self._merge_headers(headers)
        
        client = httpx.AsyncClient(timeout=self.timeout)
        try:
            response = await client.post(
                url,
                data=data,
                json=json,
                params=params,
                headers=merged_headers,
                **kwargs
            )
            return response
        finally:
            await client.aclose()
    
    async def put(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> httpx.Response:
        """
        PUT 요청
        
        Args:
            url: 요청 URL (상대 경로 또는 전체 URL)
            data: 폼 데이터
            json: JSON 데이터
            params: 쿼리 파라미터
            headers: 추가/오버라이드할 헤더
            **kwargs: httpx.AsyncClient.put()에 전달할 추가 인자
            
        Returns:
            httpx.Response 객체
        """
        if not url.startswith("http"):
            url = f"{self.base_url}{url}" if url.startswith("/") else f"{self.base_url}/{url}"
        
        merged_headers = self._merge_headers(headers)
        
        client = httpx.AsyncClient(timeout=self.timeout)
        try:
            response = await client.put(
                url,
                data=data,
                json=json,
                params=params,
                headers=merged_headers,
                **kwargs
            )
            return response
        finally:
            await client.aclose()
    
    async def delete(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> httpx.Response:
        """
        DELETE 요청
        
        Args:
            url: 요청 URL (상대 경로 또는 전체 URL)
            params: 쿼리 파라미터
            headers: 추가/오버라이드할 헤더
            **kwargs: httpx.AsyncClient.delete()에 전달할 추가 인자
            
        Returns:
            httpx.Response 객체
        """
        if not url.startswith("http"):
            url = f"{self.base_url}{url}" if url.startswith("/") else f"{self.base_url}/{url}"
        
        merged_headers = self._merge_headers(headers)
        
        client = httpx.AsyncClient(timeout=self.timeout)
        try:
            response = await client.delete(
                url,
                params=params,
                headers=merged_headers,
                **kwargs
            )
            return response
        finally:
            await client.aclose()

