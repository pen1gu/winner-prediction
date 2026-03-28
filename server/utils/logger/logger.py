import logging
import sys
import inspect
from pathlib import Path
from typing import Optional

from server.config.settings import settings


def setup_logger(
    name: str,
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Logger 설정 및 반환
    
    Args:
        name: Logger 이름 (보통 __name__ 사용)
        log_level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 로그 파일 경로 (None이면 파일 로깅 안 함)
        format_string: 로그 포맷 문자열
        
    Returns:
        설정된 Logger 인스턴스
    """
    logger = logging.getLogger(name)
    
    # 이미 핸들러가 설정되어 있으면 재설정하지 않음
    if logger.handlers:
        return logger
    
    # 로그 레벨 설정
    level = log_level or settings.log_level
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # 포맷 설정
    formatter = logging.Formatter(
        format_string or settings.log_format,
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # 콘솔 핸들러 (항상 추가)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logger.level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 파일 핸들러 (log_file이 지정된 경우)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(logger.level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    Logger 인스턴스 가져오기 (간편 함수)
    
    Args:
        name: Logger 이름 (None이면 호출한 모듈의 __name__ 사용)
        
    Returns:
        Logger 인스턴스
    """
    if name is None:
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get("__name__", "root")
    
    return setup_logger(name)

