"""
Tests for Batch Processing Modules
"""

import pytest
import time
from pathlib import Path

from core.batch.processor import BatchProcessor
from core.batch.queue import JobQueue, Job
from core.batch.progress import ProgressTracker
from core.batch.error_handler import ErrorHandler
from core.batch.results import ResultAggregator
from core.batch.pipeline import Pipeline, PipelineStage


def dummy_task(value):
    """더미 작업 함수"""
    time.sleep(0.01)
    return value * 2


def failing_task():
    """실패하는 작업 함수"""
    raise ValueError("테스트 오류")


class TestJobQueue:
    """JobQueue 테스트"""

    def test_init(self):
        """초기화 테스트"""
        queue = JobQueue()
        assert len(queue) == 0

    def test_add_job(self):
        """작업 추가 테스트"""
        queue = JobQueue()
        job = Job(job_id="test_1", func=dummy_task, args=(5,))

        queue.add(job)

        assert len(queue) == 1
        assert queue.get("test_1") == job

    def test_duplicate_job_id(self):
        """중복 작업 ID 테스트"""
        queue = JobQueue()
        job1 = Job(job_id="test_1", func=dummy_task)
        job2 = Job(job_id="test_1", func=dummy_task)

        queue.add(job1)

        with pytest.raises(ValueError):
            queue.add(job2)

    def test_get_by_status(self):
        """상태별 작업 조회 테스트"""
        queue = JobQueue()

        job1 = Job(job_id="job_1", func=dummy_task, status="pending")
        job2 = Job(job_id="job_2", func=dummy_task, status="completed")
        job3 = Job(job_id="job_3", func=dummy_task, status="pending")

        queue.add(job1)
        queue.add(job2)
        queue.add(job3)

        pending_jobs = queue.get_by_status("pending")
        assert len(pending_jobs) == 2

        completed_jobs = queue.get_by_status("completed")
        assert len(completed_jobs) == 1

    def test_remove_job(self):
        """작업 제거 테스트"""
        queue = JobQueue()
        job = Job(job_id="test_1", func=dummy_task)

        queue.add(job)
        assert len(queue) == 1

        success = queue.remove("test_1")
        assert success == True
        assert len(queue) == 0


class TestProgressTracker:
    """ProgressTracker 테스트"""

    def test_init(self):
        """초기화 테스트"""
        tracker = ProgressTracker()
        assert tracker.total == 0
        assert tracker.current == 0

    def test_start_and_update(self):
        """시작 및 업데이트 테스트"""
        tracker = ProgressTracker()
        tracker.start(total=10)

        assert tracker.total == 10
        assert tracker.current == 0

        tracker.update(3)
        assert tracker.current == 3

        tracker.update(7)
        assert tracker.current == 10

    def test_get_progress(self):
        """진행률 정보 조회 테스트"""
        tracker = ProgressTracker()
        tracker.start(total=100)
        tracker.update(25)

        progress = tracker.get_progress()

        assert progress["total"] == 100
        assert progress["current"] == 25
        assert progress["percentage"] == 25.0


class TestErrorHandler:
    """ErrorHandler 테스트"""

    def test_init(self):
        """초기화 테스트"""
        handler = ErrorHandler(max_retries=3)
        assert handler.max_retries == 3
        assert len(handler.errors) == 0

    def test_handle_error(self):
        """오류 처리 테스트"""
        handler = ErrorHandler()
        job = Job(job_id="test_1", func=dummy_task)
        error = ValueError("테스트 오류")

        handler.handle_error(job, error)

        assert len(handler.errors) == 1
        assert handler.errors[0]["job_id"] == "test_1"
        assert "ValueError" in handler.errors[0]["error_type"]

    def test_should_retry(self):
        """재시도 여부 테스트"""
        handler = ErrorHandler(max_retries=3)
        job = Job(job_id="test_1", func=dummy_task)

        assert handler.should_retry(job, attempt=0) == True
        assert handler.should_retry(job, attempt=2) == True
        assert handler.should_retry(job, attempt=3) == False


class TestResultAggregator:
    """ResultAggregator 테스트"""

    def test_init(self):
        """초기화 테스트"""
        aggregator = ResultAggregator()
        assert len(aggregator.results) == 0
        assert len(aggregator.errors) == 0

    def test_add_result(self):
        """결과 추가 테스트"""
        aggregator = ResultAggregator()
        aggregator.add_result("job_1", {"value": 42})

        assert aggregator.get_result("job_1") == {"value": 42}

    def test_add_error(self):
        """오류 추가 테스트"""
        aggregator = ResultAggregator()
        aggregator.add_error("job_1", "테스트 오류")

        assert aggregator.get_error("job_1") == "테스트 오류"

    def test_get_summary(self):
        """요약 정보 테스트"""
        aggregator = ResultAggregator()

        aggregator.add_result("job_1", {"value": 1})
        aggregator.add_result("job_2", {"value": 2})
        aggregator.add_error("job_3", "오류")

        summary = aggregator.get_summary()

        assert summary["total_count"] == 3
        assert summary["success_count"] == 2
        assert summary["error_count"] == 1
        assert summary["success_rate"] == pytest.approx(66.666, abs=0.01)


class TestBatchProcessor:
    """BatchProcessor 테스트"""

    def test_init(self):
        """초기화 테스트"""
        processor = BatchProcessor(max_workers=2)
        assert processor.max_workers == 2

    def test_add_job(self):
        """작업 추가 테스트"""
        processor = BatchProcessor()
        job = processor.add_job(
            job_id="test_1",
            func=dummy_task,
            args=(5,),
        )

        assert job.job_id == "test_1"
        assert len(processor.job_queue.jobs) == 1

    def test_process_all_success(self):
        """전체 작업 처리 테스트 (성공)"""
        processor = BatchProcessor(max_workers=2, show_progress=False)

        # 작업 추가
        for i in range(5):
            processor.add_job(
                job_id=f"job_{i+1}",
                func=dummy_task,
                args=(i,),
            )

        # 실행
        summary = processor.process_all()

        assert summary["total_count"] == 5
        assert summary["success_count"] == 5
        assert summary["error_count"] == 0

    def test_process_all_with_errors(self):
        """전체 작업 처리 테스트 (오류 포함)"""
        processor = BatchProcessor(
            max_workers=2,
            continue_on_error=True,
            show_progress=False,
        )

        # 정상 작업
        processor.add_job(job_id="job_1", func=dummy_task, args=(1,))
        processor.add_job(job_id="job_2", func=dummy_task, args=(2,))

        # 실패하는 작업
        processor.add_job(job_id="job_3", func=failing_task)

        # 실행
        summary = processor.process_all()

        assert summary["total_count"] == 3
        assert summary["success_count"] == 2
        assert summary["error_count"] == 1

    def test_job_dependencies(self):
        """작업 의존성 테스트"""
        processor = BatchProcessor(max_workers=2, show_progress=False)

        # job_2는 job_1에 의존
        processor.add_job(job_id="job_1", func=dummy_task, args=(1,))
        processor.add_job(
            job_id="job_2",
            func=dummy_task,
            args=(2,),
            dependencies=["job_1"],
        )

        summary = processor.process_all()

        assert summary["success_count"] == 2


class TestPipeline:
    """Pipeline 테스트"""

    def test_init(self):
        """초기화 테스트"""
        pipeline = Pipeline(name="test_pipeline")
        assert pipeline.name == "test_pipeline"
        assert len(pipeline.stages) == 0

    def test_add_stage(self):
        """스테이지 추가 테스트"""
        pipeline = Pipeline(name="test")

        def stage_func(data):
            return data + 1

        pipeline.add_stage("stage_1", stage_func)

        assert len(pipeline.stages) == 1
        assert pipeline.stages[0].name == "stage_1"

    def test_execute(self):
        """파이프라인 실행 테스트"""
        pipeline = Pipeline(name="test")

        def add_one(data):
            return data + 1

        def multiply_two(data):
            return data * 2

        pipeline.add_stage("add", add_one)
        pipeline.add_stage("multiply", multiply_two)

        result = pipeline.execute(5)

        # (5 + 1) * 2 = 12
        assert result == 12

    def test_disable_stage(self):
        """스테이지 비활성화 테스트"""
        pipeline = Pipeline(name="test")

        def add_one(data):
            return data + 1

        def multiply_two(data):
            return data * 2

        pipeline.add_stage("add", add_one)
        pipeline.add_stage("multiply", multiply_two)

        # multiply 스테이지 비활성화
        pipeline.disable_stage("multiply")

        result = pipeline.execute(5)

        # 5 + 1 = 6 (multiply는 실행되지 않음)
        assert result == 6


class TestPipelineStage:
    """PipelineStage 테스트"""

    def test_init(self):
        """초기화 테스트"""
        def func(data):
            return data

        stage = PipelineStage("test_stage", func)

        assert stage.name == "test_stage"
        assert stage.enabled == True

    def test_execute(self):
        """스테이지 실행 테스트"""
        def double(data, multiplier=2):
            return data * multiplier

        stage = PipelineStage("double", double, params={"multiplier": 3})

        result = stage.execute(5)

        assert result == 15

    def test_disabled_stage(self):
        """비활성화된 스테이지 테스트"""
        def double(data):
            return data * 2

        stage = PipelineStage("double", double, enabled=False)

        result = stage.execute(5)

        # 비활성화되어 있으므로 입력값 그대로 반환
        assert result == 5
