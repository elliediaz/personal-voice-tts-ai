"""
Energy-based Matching Algorithm

에너지 기반 매칭 알고리즘입니다.
"""

from typing import List
import numpy as np
import librosa
from tqdm import tqdm

from algorithms.base import BaseSimilarityAlgorithm, SimilarityMatch
from utils.logging import get_logger

logger = get_logger(__name__)


class EnergySimilarity(BaseSimilarityAlgorithm):
    """
    에너지 기반 유사도 알고리즘.

    RMS 에너지 엔벨로프를 비교하여 유사도를 계산합니다.
    """

    def __init__(
        self,
        frame_length: int = 2048,
        hop_length: int = 512,
        normalize_energy: bool = True,
        **kwargs
    ):
        """
        EnergySimilarity를 초기화합니다.

        Args:
            frame_length: 프레임 길이
            hop_length: 홉 길이
            normalize_energy: 에너지 정규화 여부
            **kwargs: 기본 클래스 파라미터
        """
        super().__init__(**kwargs)

        self.frame_length = frame_length
        self.hop_length = hop_length
        self.normalize_energy = normalize_energy

        logger.info(f"EnergySimilarity 초기화 완료")

    def _extract_energy(
        self,
        audio: np.ndarray,
    ) -> np.ndarray:
        """
        오디오의 RMS 에너지를 추출합니다.

        Args:
            audio: 오디오 데이터

        Returns:
            np.ndarray: RMS 에너지 (shape: (n_frames,))
        """
        energy = librosa.feature.rms(
            y=audio,
            frame_length=self.frame_length,
            hop_length=self.hop_length,
        )[0]

        if self.normalize_energy:
            # 정규화
            energy = (energy - np.mean(energy)) / (np.std(energy) + 1e-8)

        return energy

    def compute_similarity(
        self,
        target_audio: np.ndarray,
        source_audio: np.ndarray,
        target_sr: int,
        source_sr: int,
    ) -> float:
        """
        두 오디오 간의 에너지 기반 유사도를 계산합니다.
        """
        self._validate_audio(target_audio, target_sr, "target_audio")
        self._validate_audio(source_audio, source_sr, "source_audio")

        # 에너지 추출
        target_energy = self._extract_energy(target_audio)
        source_energy = self._extract_energy(source_audio)

        # 길이 맞추기
        min_len = min(len(target_energy), len(source_energy))
        target_energy = target_energy[:min_len]
        source_energy = source_energy[:min_len]

        # 상관 계수 기반 유사도
        correlation = np.corrcoef(target_energy, source_energy)[0, 1]
        similarity = abs(correlation)

        return similarity

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
        """
        self._validate_audio(target_audio, target_sr, "target_audio")
        self._validate_audio(source_audio, source_sr, "source_audio")

        target_duration = len(target_audio) / target_sr
        window_duration = min(target_duration, self.segment_max_length)
        window_samples = int(window_duration * source_sr)
        step_samples = window_samples // 2

        matches = []
        num_windows = (len(source_audio) - window_samples) // step_samples + 1

        target_energy = self._extract_energy(target_audio)

        for i in tqdm(range(num_windows), desc="Searching segments", disable=num_windows < 10):
            start_sample = i * step_samples
            end_sample = start_sample + window_samples

            if end_sample > len(source_audio):
                break

            window_audio = source_audio[start_sample:end_sample]
            window_energy = self._extract_energy(window_audio)

            # 길이 맞추기
            min_len = min(len(target_energy), len(window_energy))
            target_energy_trim = target_energy[:min_len]
            window_energy_trim = window_energy[:min_len]

            # 유사도 계산
            correlation = np.corrcoef(target_energy_trim, window_energy_trim)[0, 1]
            similarity = abs(correlation)

            if similarity >= self.similarity_threshold:
                match = SimilarityMatch(
                    target_start=0.0,
                    target_end=target_duration,
                    source_start=start_sample / source_sr,
                    source_end=end_sample / source_sr,
                    similarity=similarity,
                    confidence=1.0,
                    metadata={'correlation': correlation}
                )
                matches.append(match)

        return self._filter_matches(matches, top_k)


__all__ = ["EnergySimilarity"]
