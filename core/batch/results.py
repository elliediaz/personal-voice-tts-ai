"""
Result Aggregator

결과 집계 모듈
"""

import logging
from typing import Dict, List, Any
from pathlib import Path
import json
import csv
from datetime import datetime

logger = logging.getLogger(__name__)


class ResultAggregator:
    """결과 집계 클래스"""

    def __init__(self):
        self.results: Dict[str, Any] = {}
        self.errors: Dict[str, str] = {}

        logger.info("ResultAggregator 초기화")

    def add_result(self, job_id: str, result: Any):
        """
        작업 결과 추가

        Args:
            job_id: 작업 ID
            result: 작업 결과
        """
        self.results[job_id] = result
        logger.debug(f"결과 추가: {job_id}")

    def add_error(self, job_id: str, error: str):
        """
        작업 오류 추가

        Args:
            job_id: 작업 ID
            error: 오류 메시지
        """
        self.errors[job_id] = error
        logger.debug(f"오류 추가: {job_id}")

    def get_result(self, job_id: str) -> Any:
        """
        작업 결과 조회

        Args:
            job_id: 작업 ID

        Returns:
            작업 결과 또는 None
        """
        return self.results.get(job_id)

    def get_error(self, job_id: str) -> str:
        """
        작업 오류 조회

        Args:
            job_id: 작업 ID

        Returns:
            오류 메시지 또는 None
        """
        return self.errors.get(job_id)

    def get_summary(self) -> Dict[str, Any]:
        """
        결과 요약 정보 반환

        Returns:
            요약 정보 딕셔너리
        """
        total_count = len(self.results) + len(self.errors)
        success_count = len(self.results)
        error_count = len(self.errors)

        return {
            "total_count": total_count,
            "success_count": success_count,
            "error_count": error_count,
            "success_rate": (success_count / total_count * 100) if total_count > 0 else 0,
        }

    def save_json(self, filepath: Path):
        """
        결과를 JSON 파일로 저장

        Args:
            filepath: 저장 경로
        """
        data = {
            "summary": self.get_summary(),
            "results": {k: self._serialize_result(v) for k, v in self.results.items()},
            "errors": self.errors,
            "saved_at": datetime.now().isoformat(),
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"결과 저장 (JSON): {filepath}")

    def save_csv(self, filepath: Path):
        """
        결과를 CSV 파일로 저장

        Args:
            filepath: 저장 경로
        """
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # 헤더
            writer.writerow(["Job ID", "Status", "Result/Error"])

            # 성공한 작업
            for job_id, result in self.results.items():
                writer.writerow([job_id, "Success", self._serialize_result(result)])

            # 실패한 작업
            for job_id, error in self.errors.items():
                writer.writerow([job_id, "Failed", error])

        logger.info(f"결과 저장 (CSV): {filepath}")

    def _serialize_result(self, result: Any) -> Any:
        """결과를 직렬화 가능한 형태로 변환"""
        if isinstance(result, (str, int, float, bool, type(None))):
            return result
        elif isinstance(result, dict):
            return {k: self._serialize_result(v) for k, v in result.items()}
        elif isinstance(result, (list, tuple)):
            return [self._serialize_result(item) for item in result]
        else:
            return str(result)

    def clear(self):
        """결과 초기화"""
        self.results.clear()
        self.errors.clear()
        logger.info("결과 초기화")

    def __repr__(self) -> str:
        summary = self.get_summary()
        return (
            f"ResultAggregator(total={summary['total_count']}, "
            f"success={summary['success_count']}, "
            f"errors={summary['error_count']})"
        )
