"""
Base Similarity Algorithm

모든 유사도 알고리즘의 기본 클래스를 정의합니다.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import numpy as np

from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SimilarityMatch:
    """
    유사도 매칭 결과를 저장하는 데이터 클래스.

    Attributes:
        target_start: 타겟 오디오 시작 시간 (초)
        target_end: 타겟 오디오 종료 시간 (초)
        source_start: 소스 오디오 시작 시간 (초)
        source_end: 소스 오디오 종료 시간 (초)
        similarity: 유사도 점수 (0.0 ~ 1.0)
        confidence: 신뢰도 점수 (0.0 ~ 1.0)
        metadata: 추가 메타데이터
    """

    target_start: float
    target_end: float
    source_start: float
    source_end: float
    similarity: float
    confidence: float = 1.0
    metadata: Optional[Dict[str, Any]] = None

    @property
    def target_duration(self) -> float:
        """타겟 세그먼트 길이"""
        return self.target_end - self.target_start

    @property
    def source_duration(self) -> float:
        """소스 세그먼트 길이"""
        return self.source_end - self.source_start

    def __repr__(self) -> str:
        return (
            f"SimilarityMatch("
            f"target=[{self.target_start:.2f}, {self.target_end:.2f}]s, "
            f"source=[{self.source_start:.2f}, {self.source_end:.2f}]s, "
            f"similarity={self.similarity:.3f}, "
            f"confidence={self.confidence:.3f})"
        )


class BaseSimilarityAlgorithm(ABC):
    """
    유사도 알고리즘의 추상 기본 클래스.

    모든 유사도 알고리즘은 이 클래스를 상속받아 구현해야 합니다.
    """

    def __init__(
        self,
        similarity_threshold: float = 0.7,
        confidence_threshold: float = 0.5,
        segment_min_length: float = 0.1,
        segment_max_length: float = 10.0,
        **kwargs
    ):
        """
        BaseSimilarityAlgorithm을 초기화합니다.

        Args:
            similarity_threshold: 유사도 임계값 (0.0 ~ 1.0)
            confidence_threshold: 신뢰도 임계값 (0.0 ~ 1.0)
            segment_min_length: 최소 세그먼트 길이 (초)
            segment_max_length: 최대 세그먼트 길이 (초)
            **kwargs: 추가 파라미터
        """
        self.similarity_threshold = similarity_threshold
        self.confidence_threshold = confidence_threshold
        self.segment_min_length = segment_min_length
        self.segment_max_length = segment_max_length
        self.config = kwargs

        logger.debug(
            f"{self.__class__.__name__} 초기화: "
            f"similarity_threshold={similarity_threshold}, "
            f"confidence_threshold={confidence_threshold}"
        )

    @abstractmethod
    def compute_similarity(
        self,
        target_audio: np.ndarray,
        source_audio: np.ndarray,
        target_sr: int,
        source_sr: int,
    ) -> float:
        """
        두 오디오 간의 전체 유사도를 계산합니다.

        Args:
            target_audio: 타겟 오디오 데이터
            source_audio: 소스 오디오 데이터
            target_sr: 타겟 샘플링 레이트
            source_sr: 소스 샘플링 레이트

        Returns:
            float: 유사도 점수 (0.0 ~ 1.0)
        """
        pass

    @abstractmethod
    def find_similar_segments(
        self,
        target_audio: np.ndarray,
        source_audio: np.ndarray,
        target_sr: int,
        source_sr: int,
        top_k: int = 10,
    ) -> List[SimilarityMatch]:
        """
        타겟 오디오와 유사한 소스 오디오의 세그먼트를 찾습니다.

        Args:
            target_audio: 타겟 오디오 데이터
            source_audio: 소스 오디오 데이터
            target_sr: 타겟 샘플링 레이트
            source_sr: 소스 샘플링 레이트
            top_k: 반환할 최대 매치 수

        Returns:
            List[SimilarityMatch]: 유사 세그먼트 리스트 (유사도 높은 순)
        """
        pass

    def _validate_audio(
        self,
        audio: np.ndarray,
        sr: int,
        name: str = "audio",
    ) -> None:
        """
        오디오 데이터를 검증합니다.

        Args:
            audio: 오디오 데이터
            sr: 샘플링 레이트
            name: 오디오 이름 (로깅용)

        Raises:
            ValueError: 잘못된 오디오 데이터
        """
        if audio is None or len(audio) == 0:
            raise ValueError(f"{name}가 비어있습니다.")

        if sr <= 0:
            raise ValueError(f"잘못된 샘플링 레이트: {sr}")

        duration = len(audio) / sr
        if duration < self.segment_min_length:
            raise ValueError(
                f"{name}의 길이({duration:.2f}초)가 "
                f"최소 세그먼트 길이({self.segment_min_length}초)보다 짧습니다."
            )

    def _filter_matches(
        self,
        matches: List[SimilarityMatch],
        top_k: Optional[int] = None,
    ) -> List[SimilarityMatch]:
        """
        매칭 결과를 필터링하고 정렬합니다.

        Args:
            matches: 매칭 결과 리스트
            top_k: 반환할 최대 개수

        Returns:
            List[SimilarityMatch]: 필터링 및 정렬된 매칭 결과
        """
        # 임계값 필터링
        filtered = [
            m for m in matches
            if m.similarity >= self.similarity_threshold
            and m.confidence >= self.confidence_threshold
        ]

        # 유사도 기준 정렬 (높은 순)
        sorted_matches = sorted(
            filtered,
            key=lambda x: (x.similarity, x.confidence),
            reverse=True,
        )

        # top_k 제한
        if top_k is not None and top_k > 0:
            sorted_matches = sorted_matches[:top_k]

        return sorted_matches

    def get_name(self) -> str:
        """알고리즘 이름을 반환합니다."""
        return self.__class__.__name__

    def get_config(self) -> Dict[str, Any]:
        """현재 설정을 반환합니다."""
        return {
            'algorithm': self.get_name(),
            'similarity_threshold': self.similarity_threshold,
            'confidence_threshold': self.confidence_threshold,
            'segment_min_length': self.segment_min_length,
            'segment_max_length': self.segment_max_length,
            **self.config,
        }

    def __repr__(self) -> str:
        return f"{self.get_name()}(threshold={self.similarity_threshold:.2f})"


__all__ = ["BaseSimilarityAlgorithm", "SimilarityMatch"]
