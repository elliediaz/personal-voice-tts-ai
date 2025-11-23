"""
Random Matching Algorithm

랜덤 매칭 알고리즘 (베이스라인 비교용)입니다.
"""

from typing import List
import numpy as np

from algorithms.base import BaseSimilarityAlgorithm, SimilarityMatch
from utils.logging import get_logger

logger = get_logger(__name__)


class RandomMatcher(BaseSimilarityAlgorithm):
    """
    랜덤 매칭 알고리즘.

    베이스라인 비교를 위한 랜덤 세그먼트 선택 알고리즘입니다.
    """

    def __init__(
        self,
        seed: int = 42,
        weighted: bool = False,
        **kwargs
    ):
        """
        RandomMatcher를 초기화합니다.

        Args:
            seed: 랜덤 시드
            weighted: 가중치 랜덤 사용 여부 (에너지 기반)
            **kwargs: 기본 클래스 파라미터
        """
        super().__init__(**kwargs)

        self.seed = seed
        self.weighted = weighted
        self.rng = np.random.RandomState(seed)

        logger.info(f"RandomMatcher 초기화 완료 (seed={seed}, weighted={weighted})")

    def compute_similarity(
        self,
        target_audio: np.ndarray,
        source_audio: np.ndarray,
        target_sr: int,
        source_sr: int,
    ) -> float:
        """
        랜덤 유사도 점수를 반환합니다.
        """
        # 0.0 ~ 1.0 사이의 랜덤 값
        return self.rng.uniform(0.0, 1.0)

    def find_similar_segments(
        self,
        target_audio: np.ndarray,
        source_audio: np.ndarray,
        target_sr: int,
        source_sr: int,
        top_k: int = 10,
    ) -> List[SimilarityMatch]:
        """
        랜덤하게 세그먼트를 선택합니다.
        """
        self._validate_audio(target_audio, target_sr, "target_audio")
        self._validate_audio(source_audio, source_sr, "source_audio")

        target_duration = len(target_audio) / target_sr
        window_duration = min(target_duration, self.segment_max_length)
        window_samples = int(window_duration * source_sr)

        matches = []

        # top_k개의 랜덤 위치 선택
        max_start = len(source_audio) - window_samples
        if max_start <= 0:
            logger.warning("소스 오디오가 너무 짧습니다.")
            return []

        # 가중치 계산 (weighted인 경우)
        if self.weighted:
            # 간단한 에너지 기반 가중치
            import librosa
            energy = librosa.feature.rms(y=source_audio, frame_length=2048, hop_length=512)[0]
            frame_to_sample = 512  # hop_length

            # 각 프레임의 가중치
            weights = []
            for i in range(0, max_start, window_samples // 2):
                frame_start = i // frame_to_sample
                frame_end = min((i + window_samples) // frame_to_sample, len(energy))
                if frame_end > frame_start:
                    avg_energy = np.mean(energy[frame_start:frame_end])
                    weights.append(avg_energy)
                else:
                    weights.append(0.0)

            if not weights or sum(weights) == 0:
                weights = None
            else:
                weights = np.array(weights)
                weights = weights / np.sum(weights)

            # 가중치 기반 샘플링
            num_positions = len(weights) if weights is not None else (max_start // (window_samples // 2))
            selected_indices = self.rng.choice(
                num_positions,
                size=min(top_k, num_positions),
                replace=False,
                p=weights
            )
            start_samples = [idx * (window_samples // 2) for idx in selected_indices]
        else:
            # 균등 랜덤 샘플링
            start_samples = self.rng.choice(
                range(0, max_start, window_samples // 4),
                size=min(top_k, max_start // (window_samples // 4)),
                replace=False,
            )

        # 매치 생성
        for start_sample in start_samples:
            end_sample = start_sample + window_samples

            # 랜덤 유사도 점수
            similarity = self.rng.uniform(0.5, 1.0)

            match = SimilarityMatch(
                target_start=0.0,
                target_end=target_duration,
                source_start=start_sample / source_sr,
                source_end=end_sample / source_sr,
                similarity=similarity,
                confidence=self.rng.uniform(0.5, 1.0),
                metadata={'random': True, 'weighted': self.weighted}
            )
            matches.append(match)

        # 유사도 기준 정렬
        matches.sort(key=lambda x: x.similarity, reverse=True)

        return matches[:top_k]


__all__ = ["RandomMatcher"]
