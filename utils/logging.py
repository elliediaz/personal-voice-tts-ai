"""
Logging Utilities

로깅 설정 및 유틸리티 함수를 제공합니다.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
import colorlog


def setup_logger(
    name: str,
    level: str = "INFO",
    log_file: Optional[str] = None,
    console: bool = True,
    log_format: Optional[str] = None,
    date_format: Optional[str] = None,
) -> logging.Logger:
    """
    로거를 설정합니다.

    Args:
        name: 로거 이름
        level: 로그 레벨
        log_file: 로그 파일 경로 (선택사항)
        console: 콘솔 출력 여부
        log_format: 로그 포맷 (선택사항)
        date_format: 날짜 포맷 (선택사항)

    Returns:
        logging.Logger: 설정된 로거
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    logger.handlers.clear()

    # 기본 포맷
    if log_format is None:
        log_format = "%(log_color)s%(asctime)s - %(name)s - %(levelname)s%(reset)s - %(message)s"

    if date_format is None:
        date_format = "%Y-%m-%d %H:%M:%S"

    # 콘솔 핸들러 (색상 지원)
    if console:
        console_handler = colorlog.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))

        console_formatter = colorlog.ColoredFormatter(
            log_format,
            datefmt=date_format,
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    # 파일 핸들러
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, level.upper()))

        # 파일에는 색상 코드 제외
        file_format = log_format.replace("%(log_color)s", "").replace("%(reset)s", "")
        file_formatter = logging.Formatter(file_format, datefmt=date_format)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    이름으로 로거를 가져옵니다.

    Args:
        name: 로거 이름

    Returns:
        logging.Logger: 로거 인스턴스
    """
    return logging.getLogger(name)


__all__ = ["setup_logger", "get_logger"]
