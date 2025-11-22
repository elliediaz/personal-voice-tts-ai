"""
Batch Processor

배치 처리 메인 모듈
"""

import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import multiprocessing as mp

from core.batch.queue import JobQueue, Job
from core.batch.progress import ProgressTracker
from core.batch.results import ResultAggregator
from core.batch.error_handler import ErrorHandler

logger = logging.getLogger(__name__)


class BatchProcessor:
    """배치 처리 클래스"""

    def __init__(
        self,
        max_workers: Optional[int] = None,
        use_processes: bool = False,
        continue_on_error: bool = True,
        show_progress: bool = True,
    ):
        """
        Args:
            max_workers: 최대 워커 수 (None이면 CPU 코어 수)
            use_processes: 프로세스 사용 여부 (False면 스레드 사용)
            continue_on_error: 오류 발생 시 계속 진행 여부
            show_progress: 진행률 표시 여부
        """
        self.max_workers = max_workers or mp.cpu_count()
        self.use_processes = use_processes
        self.continue_on_error = continue_on_error
        self.show_progress = show_progress

        self.job_queue = JobQueue()
        self.progress_tracker = ProgressTracker()
        self.result_aggregator = ResultAggregator()
        self.error_handler = ErrorHandler(continue_on_error=continue_on_error)

        logger.info(
            f"BatchProcessor 초기화: max_workers={self.max_workers}, "
            f"use_processes={self.use_processes}"
        )

    def add_job(
        self,
        job_id: str,
        func: Callable,
        args: tuple = (),
        kwargs: dict = None,
        priority: int = 0,
        dependencies: List[str] = None,
    ) -> Job:
        """
        작업 추가

        Args:
            job_id: 작업 ID
            func: 실행할 함수
            args: 위치 인자
            kwargs: 키워드 인자
            priority: 우선순위 (높을수록 먼저 실행)
            dependencies: 의존하는 작업 ID 리스트

        Returns:
            생성된 Job 객체
        """
        job = Job(
            job_id=job_id,
            func=func,
            args=args,
            kwargs=kwargs or {},
            priority=priority,
            dependencies=dependencies or [],
        )
        self.job_queue.add(job)
        logger.debug(f"작업 추가: {job_id}, priority={priority}")
        return job

    def process_all(self) -> Dict[str, Any]:
        """
        모든 작업 처리

        Returns:
            처리 결과 딕셔너리
        """
        start_time = time.time()
        logger.info(f"배치 처리 시작: {len(self.job_queue.jobs)}개 작업")

        # 진행률 추적 초기화
        if self.show_progress:
            self.progress_tracker.start(total=len(self.job_queue.jobs))

        # Executor 선택
        executor_class = ProcessPoolExecutor if self.use_processes else ThreadPoolExecutor

        with executor_class(max_workers=self.max_workers) as executor:
            # 의존성 해결 및 작업 제출
            futures = {}
            completed_jobs = set()

            while self.job_queue.has_pending():
                # 실행 가능한 작업 찾기 (의존성이 모두 완료된 작업)
                ready_jobs = self._get_ready_jobs(completed_jobs)

                for job in ready_jobs:
                    if job.job_id not in futures:
                        future = executor.submit(self._execute_job, job)
                        futures[future] = job
                        job.status = "running"
                        logger.debug(f"작업 제출: {job.job_id}")

                # 완료된 작업 처리
                done_futures = [f for f in futures if f.done()]
                for future in done_futures:
                    job = futures.pop(future)
                    try:
                        result = future.result()
                        job.status = "completed"
                        job.result = result
                        completed_jobs.add(job.job_id)

                        self.result_aggregator.add_result(job.job_id, result)

                        if self.show_progress:
                            self.progress_tracker.update(1)

                        logger.info(f"작업 완료: {job.job_id}")

                    except Exception as e:
                        job.status = "failed"
                        job.error = str(e)

                        self.error_handler.handle_error(job, e)
                        self.result_aggregator.add_error(job.job_id, str(e))

                        if self.show_progress:
                            self.progress_tracker.update(1)

                        logger.error(f"작업 실패: {job.job_id}, 오류: {str(e)}")

                        if not self.continue_on_error:
                            # 나머지 작업 취소
                            for f in futures:
                                f.cancel()
                            raise

                # 짧은 대기
                if not done_futures and futures:
                    time.sleep(0.1)

        # 진행률 추적 종료
        if self.show_progress:
            self.progress_tracker.finish()

        total_time = time.time() - start_time

        # 결과 집계
        summary = self.result_aggregator.get_summary()
        summary["total_time"] = total_time
        summary["jobs_per_second"] = len(self.job_queue.jobs) / total_time if total_time > 0 else 0

        logger.info(
            f"배치 처리 완료: {summary['success_count']}/{summary['total_count']} 성공, "
            f"소요 시간: {total_time:.2f}초"
        )

        return summary

    def _get_ready_jobs(self, completed_jobs: set) -> List[Job]:
        """
        실행 가능한 작업 목록 반환 (의존성이 모두 완료된 작업)

        Args:
            completed_jobs: 완료된 작업 ID 집합

        Returns:
            실행 가능한 Job 리스트
        """
        ready = []
        for job in self.job_queue.jobs:
            if job.status == "pending":
                # 모든 의존성이 완료되었는지 확인
                if all(dep in completed_jobs for dep in job.dependencies):
                    ready.append(job)

        # 우선순위로 정렬
        ready.sort(key=lambda j: j.priority, reverse=True)
        return ready

    def _execute_job(self, job: Job) -> Any:
        """
        작업 실행

        Args:
            job: 실행할 Job 객체

        Returns:
            작업 결과
        """
        logger.debug(f"작업 실행 시작: {job.job_id}")
        start_time = time.time()

        try:
            result = job.func(*job.args, **job.kwargs)
            execution_time = time.time() - start_time
            logger.debug(f"작업 실행 완료: {job.job_id}, 소요 시간: {execution_time:.2f}초")
            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"작업 실행 실패: {job.job_id}, 오류: {str(e)}, "
                f"소요 시간: {execution_time:.2f}초"
            )
            raise

    def clear(self):
        """작업 큐 및 결과 초기화"""
        self.job_queue.clear()
        self.result_aggregator.clear()
        logger.info("배치 프로세서 초기화")

    def __repr__(self) -> str:
        return (
            f"BatchProcessor(max_workers={self.max_workers}, "
            f"use_processes={self.use_processes}, "
            f"jobs={len(self.job_queue.jobs)})"
        )
