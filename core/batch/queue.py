"""
Job Queue

작업 큐 관리 모듈
"""

import logging
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Job:
    """작업 클래스"""

    job_id: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    priority: int = 0
    dependencies: List[str] = field(default_factory=list)
    status: str = "pending"  # pending, running, completed, failed
    result: Any = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """딕셔너리로 변환 (직렬화 가능한 형태)"""
        return {
            "job_id": self.job_id,
            "func_name": self.func.__name__ if hasattr(self.func, "__name__") else str(self.func),
            "priority": self.priority,
            "dependencies": self.dependencies,
            "status": self.status,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class JobQueue:
    """작업 큐 클래스"""

    def __init__(self):
        self.jobs: List[Job] = []
        logger.info("JobQueue 초기화")

    def add(self, job: Job):
        """
        작업 추가

        Args:
            job: Job 객체
        """
        if self.get(job.job_id):
            raise ValueError(f"중복된 작업 ID: {job.job_id}")

        self.jobs.append(job)
        logger.debug(f"작업 추가: {job.job_id}")

    def get(self, job_id: str) -> Optional[Job]:
        """
        작업 ID로 작업 조회

        Args:
            job_id: 작업 ID

        Returns:
            Job 객체 또는 None
        """
        for job in self.jobs:
            if job.job_id == job_id:
                return job
        return None

    def remove(self, job_id: str) -> bool:
        """
        작업 제거

        Args:
            job_id: 작업 ID

        Returns:
            제거 성공 여부
        """
        job = self.get(job_id)
        if job:
            self.jobs.remove(job)
            logger.debug(f"작업 제거: {job_id}")
            return True
        return False

    def get_by_status(self, status: str) -> List[Job]:
        """
        상태별 작업 조회

        Args:
            status: 작업 상태 (pending, running, completed, failed)

        Returns:
            Job 리스트
        """
        return [job for job in self.jobs if job.status == status]

    def has_pending(self) -> bool:
        """대기 중인 작업이 있는지 확인"""
        return any(job.status == "pending" for job in self.jobs)

    def get_pending_count(self) -> int:
        """대기 중인 작업 수"""
        return len(self.get_by_status("pending"))

    def get_running_count(self) -> int:
        """실행 중인 작업 수"""
        return len(self.get_by_status("running"))

    def get_completed_count(self) -> int:
        """완료된 작업 수"""
        return len(self.get_by_status("completed"))

    def get_failed_count(self) -> int:
        """실패한 작업 수"""
        return len(self.get_by_status("failed"))

    def clear(self):
        """모든 작업 제거"""
        self.jobs.clear()
        logger.info("작업 큐 초기화")

    def save(self, filepath: Path):
        """
        작업 큐를 파일로 저장

        Args:
            filepath: 저장 경로
        """
        data = {
            "jobs": [job.to_dict() for job in self.jobs],
            "saved_at": datetime.now().isoformat(),
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"작업 큐 저장: {filepath}")

    def __len__(self) -> int:
        return len(self.jobs)

    def __repr__(self) -> str:
        return (
            f"JobQueue(total={len(self.jobs)}, "
            f"pending={self.get_pending_count()}, "
            f"running={self.get_running_count()}, "
            f"completed={self.get_completed_count()}, "
            f"failed={self.get_failed_count()})"
        )
