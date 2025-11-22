"""
Pipeline Configuration

파이프라인 구성 모듈
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional
import yaml

from core.batch.processor import BatchProcessor

logger = logging.getLogger(__name__)


class PipelineStage:
    """파이프라인 스테이지 클래스"""

    def __init__(
        self,
        name: str,
        func: Callable,
        enabled: bool = True,
        params: Optional[Dict[str, Any]] = None,
    ):
        """
        Args:
            name: 스테이지 이름
            func: 실행할 함수
            enabled: 활성화 여부
            params: 스테이지 파라미터
        """
        self.name = name
        self.func = func
        self.enabled = enabled
        self.params = params or {}

    def execute(self, data: Any, **kwargs) -> Any:
        """
        스테이지 실행

        Args:
            data: 입력 데이터
            **kwargs: 추가 인자

        Returns:
            처리된 데이터
        """
        if not self.enabled:
            logger.debug(f"스테이지 비활성화: {self.name}")
            return data

        logger.info(f"스테이지 실행: {self.name}")

        # 파라미터 병합
        merged_params = {**self.params, **kwargs}

        # 함수 실행
        result = self.func(data, **merged_params)

        logger.info(f"스테이지 완료: {self.name}")
        return result

    def __repr__(self) -> str:
        return f"PipelineStage(name={self.name}, enabled={self.enabled})"


class Pipeline:
    """파이프라인 클래스"""

    def __init__(self, name: str):
        """
        Args:
            name: 파이프라인 이름
        """
        self.name = name
        self.stages: List[PipelineStage] = []

        logger.info(f"Pipeline 초기화: {name}")

    def add_stage(
        self,
        name: str,
        func: Callable,
        enabled: bool = True,
        params: Optional[Dict[str, Any]] = None,
    ) -> "Pipeline":
        """
        스테이지 추가

        Args:
            name: 스테이지 이름
            func: 실행할 함수
            enabled: 활성화 여부
            params: 스테이지 파라미터

        Returns:
            자기 자신 (체이닝 가능)
        """
        stage = PipelineStage(name, func, enabled, params)
        self.stages.append(stage)
        logger.debug(f"스테이지 추가: {name}")
        return self

    def execute(self, data: Any, **kwargs) -> Any:
        """
        파이프라인 실행

        Args:
            data: 입력 데이터
            **kwargs: 추가 인자

        Returns:
            최종 처리된 데이터
        """
        logger.info(f"파이프라인 실행 시작: {self.name}")

        result = data
        for stage in self.stages:
            if stage.enabled:
                result = stage.execute(result, **kwargs)

        logger.info(f"파이프라인 실행 완료: {self.name}")
        return result

    def enable_stage(self, name: str):
        """
        스테이지 활성화

        Args:
            name: 스테이지 이름
        """
        for stage in self.stages:
            if stage.name == name:
                stage.enabled = True
                logger.debug(f"스테이지 활성화: {name}")
                return
        logger.warning(f"스테이지를 찾을 수 없음: {name}")

    def disable_stage(self, name: str):
        """
        스테이지 비활성화

        Args:
            name: 스테이지 이름
        """
        for stage in self.stages:
            if stage.name == name:
                stage.enabled = False
                logger.debug(f"스테이지 비활성화: {name}")
                return
        logger.warning(f"스테이지를 찾을 수 없음: {name}")

    @classmethod
    def from_config(cls, config_path: Path) -> "Pipeline":
        """
        설정 파일에서 파이프라인 생성

        Args:
            config_path: 설정 파일 경로

        Returns:
            Pipeline 객체
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        pipeline_name = config.get("name", "pipeline")
        pipeline = cls(pipeline_name)

        # 스테이지 추가는 외부에서 함수를 주입해야 하므로
        # 여기서는 구조만 로드
        logger.info(f"설정 파일에서 파이프라인 구조 로드: {config_path}")

        return pipeline

    def __repr__(self) -> str:
        return f"Pipeline(name={self.name}, stages={len(self.stages)})"
