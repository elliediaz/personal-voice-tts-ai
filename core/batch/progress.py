"""
Progress Tracker

진행률 추적 모듈
"""

import logging
import time
from typing import Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ProgressTracker:
    """진행률 추적 클래스"""

    def __init__(self, bar_length: int = 50):
        """
        Args:
            bar_length: 프로그레스 바 길이
        """
        self.bar_length = bar_length
        self.total: int = 0
        self.current: int = 0
        self.start_time: Optional[datetime] = None
        self.last_update_time: Optional[datetime] = None

        logger.info("ProgressTracker 초기화")

    def start(self, total: int):
        """
        진행률 추적 시작

        Args:
            total: 전체 작업 수
        """
        self.total = total
        self.current = 0
        self.start_time = datetime.now()
        self.last_update_time = self.start_time

        logger.info(f"진행률 추적 시작: 전체 {total}개 작업")
        self._print_progress()

    def update(self, increment: int = 1):
        """
        진행률 업데이트

        Args:
            increment: 증가량
        """
        self.current += increment
        self.last_update_time = datetime.now()

        self._print_progress()

    def finish(self):
        """진행률 추적 종료"""
        self.current = self.total
        self._print_progress()
        print()  # 줄바꿈
        logger.info("진행률 추적 완료")

    def _print_progress(self):
        """프로그레스 바 출력"""
        if self.total == 0:
            return

        # 진행률 계산
        percentage = (self.current / self.total) * 100

        # 프로그레스 바 생성
        filled_length = int(self.bar_length * self.current // self.total)
        bar = "█" * filled_length + "░" * (self.bar_length - filled_length)

        # 남은 시간 추정
        eta_str = self._estimate_eta()

        # 출력
        print(
            f"\r진행: [{bar}] {self.current}/{self.total} "
            f"({percentage:5.1f}%) {eta_str}",
            end="",
        )

    def _estimate_eta(self) -> str:
        """남은 시간 추정"""
        if not self.start_time or self.current == 0:
            return "ETA: N/A"

        elapsed = (datetime.now() - self.start_time).total_seconds()
        rate = self.current / elapsed  # 작업/초

        if rate > 0:
            remaining = self.total - self.current
            eta_seconds = remaining / rate
            eta = timedelta(seconds=int(eta_seconds))
            return f"ETA: {eta}"
        else:
            return "ETA: N/A"

    def get_progress(self) -> dict:
        """
        진행률 정보 반환

        Returns:
            진행률 정보 딕셔너리
        """
        percentage = (self.current / self.total * 100) if self.total > 0 else 0
        elapsed = (
            (datetime.now() - self.start_time).total_seconds()
            if self.start_time
            else 0
        )

        return {
            "total": self.total,
            "current": self.current,
            "percentage": percentage,
            "elapsed_seconds": elapsed,
        }

    def __repr__(self) -> str:
        percentage = (self.current / self.total * 100) if self.total > 0 else 0
        return f"ProgressTracker({self.current}/{self.total}, {percentage:.1f}%)"
