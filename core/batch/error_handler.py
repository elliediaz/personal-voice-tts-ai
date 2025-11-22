"""
Error Handler

오류 처리 모듈
"""

import logging
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path
import json

from core.batch.queue import Job

logger = logging.getLogger(__name__)


class ErrorHandler:
    """오류 처리 클래스"""

    def __init__(
        self,
        continue_on_error: bool = True,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Args:
            continue_on_error: 오류 발생 시 계속 진행 여부
            max_retries: 최대 재시도 횟수
            retry_delay: 재시도 간격 (초)
        """
        self.continue_on_error = continue_on_error
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self.errors: List[Dict[str, Any]] = []

        logger.info(
            f"ErrorHandler 초기화: continue_on_error={continue_on_error}, "
            f"max_retries={max_retries}"
        )

    def handle_error(self, job: Job, error: Exception):
        """
        오류 처리

        Args:
            job: 실패한 Job 객체
            error: 발생한 오류
        """
        error_info = {
            "job_id": job.job_id,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.now().isoformat(),
        }

        self.errors.append(error_info)

        logger.error(
            f"작업 오류 처리: {job.job_id}, "
            f"오류: {error_info['error_type']}: {error_info['error_message']}"
        )

    def should_retry(self, job: Job, attempt: int) -> bool:
        """
        재시도 여부 결정

        Args:
            job: Job 객체
            attempt: 시도 횟수

        Returns:
            재시도 여부
        """
        return attempt < self.max_retries

    def get_error_summary(self) -> Dict[str, Any]:
        """
        오류 요약 정보 반환

        Returns:
            오류 요약 딕셔너리
        """
        error_types = {}
        for error in self.errors:
            error_type = error["error_type"]
            error_types[error_type] = error_types.get(error_type, 0) + 1

        return {
            "total_errors": len(self.errors),
            "error_types": error_types,
            "errors": self.errors,
        }

    def save_errors(self, filepath: Path):
        """
        오류 정보를 파일로 저장

        Args:
            filepath: 저장 경로
        """
        summary = self.get_error_summary()

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        logger.info(f"오류 정보 저장: {filepath}")

    def clear(self):
        """오류 정보 초기화"""
        self.errors.clear()
        logger.info("오류 정보 초기화")

    def __repr__(self) -> str:
        return f"ErrorHandler(errors={len(self.errors)}, max_retries={self.max_retries})"
