from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # FotMob API 설정
    fotmob_base_url: str = "https://www.fotmob.com"
    fotmob_api_url: str = "https://www.fotmob.com/api"
    fotmob_language: str = "ko"
    
    # HTTP 클라이언트 설정
    http_timeout: float = 30.0
    http_max_retries: int = 3
    
    # 브라우저 설정
    browser_headless: bool = True
    browser_timeout: int = 30000
    
    # User-Agent 설정
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
    
    # 로깅 설정
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# 전역 설정 인스턴스
settings = Settings()

