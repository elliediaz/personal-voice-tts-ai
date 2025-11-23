"""
Spectral Similarity Algorithm

스펙트럼 특징을 사용한 유사도 검출 알고리즘입니다.
"""

from typing import List
import numpy as np
import librosa
from tqdm import tqdm

from algorithms.base import BaseSimilarityAlgorithm, SimilarityMatch
from utils.logging import get_logger

logger = get_logger(__name__)


class SpectralSimilarity(BaseSimilarityAlgorithm):
    """
    스펙트럼 기반 유사도 알고리즘.

    스펙트럼 중심, 롤오프, 대비 등의 특징을 사용하여 유사도를 계산합니다.
    """

    def __init__(
        self,
        n_fft: int = 2048,
        hop_length: int = 512,
        centroid_weight: float = 0.3,
        rolloff_weight: float = 0.3,
        contrast_weight: float = 0.2,
        bandwidth_weight: float = 0.2,
        **kwargs
    ):
        """
        SpectralSimilarity를 초기화합니다.

        Args:
            n_fft: FFT 윈도우 크기
            hop_length: 홉 길이
            centroid_weight: 스펙트럼 중심 가중치
            rolloff_weight: 스펙트럼 롤오프 가중치
            contrast_weight: 스펙트럼 대비 가중치
            bandwidth_weight: 스펙트럼 대역폭 가중치
            **kwargs: 기본 클래스 파라미터
        """
        super().__init__(**kwargs)

        self.n_fft = n_fft
        self.hop_length = hop_length

        # 가중치 정규화
        total_weight = centroid_weight + rolloff_weight + contrast_weight + bandwidth_weight
        self.centroid_weight = centroid_weight / total_weight
        self.rolloff_weight = rolloff_weight / total_weight
        self.contrast_weight = contrast_weight / total_weight
        self.bandwidth_weight = bandwidth_weight / total_weight

        logger.info(f"SpectralSimilarity 초기화 완료")

    def _extract_spectral_features(
        self,
        audio: np.ndarray,
        sr: int,
    ) -> dict:
        """
        스펙트럼 특징을 추출합니다.

        Args:
            audio: 오디오 데이터
            sr: 샘플링 레이트

        Returns:
            dict: 스펙트럼 특징 딕셔너리
        """
        features = {}

        # 스펙트럼 중심
        features['centroid'] = librosa.feature.spectral_centroid(
            y=audio,
            sr=sr,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
        )[0]

        # 스펙트럼 롤오프
        features['rolloff'] = librosa.feature.spectral_rolloff(
            y=audio,
            sr=sr,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
        )[0]

        # 스펙트럼 대비
        features['contrast'] = librosa.feature.spectral_contrast(
            y=audio,
            sr=sr,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
        )

        # 스펙트럼 대역폭
        features['bandwidth'] = librosa.feature.spectral_bandwidth(
            y=audio,
            sr=sr,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
        )[0]

        return features

    def _compute_feature_similarity(
        self,
        feat1: np.ndarray,
        feat2: np.ndarray,
    ) -> float:
        """
        두 특징 간의 유사도를 계산합니다.

        Args:
            feat1: 첫 번째 특징
            feat2: 두 번째 특징

        Returns:
            float: 유사도 (0.0 ~ 1.0)
        """
        # 길이 맞추기
        min_len = min(len(feat1), len(feat2))
        feat1 = feat1[:min_len]
        feat2 = feat2[:min_len]

        # 정규화
        feat1_norm = (feat1 - np.mean(feat1)) / (np.std(feat1) + 1e-8)
        feat2_norm = (feat2 - np.mean(feat2)) / (np.std(feat2) + 1e-8)

        # 상관 계수
        correlation = np.corrcoef(feat1_norm, feat2_norm)[0, 1]

        # 유사도로 변환 (절대값 사용)
        similarity = abs(correlation)

        return similarity

    def compute_similarity(
        self,
        target_audio: np.ndarray,
        source_audio: np.ndarray,
        target_sr: int,
        source_sr: int,
    ) -> float:
        """
        두 오디오 간의 스펙트럼 기반 유사도를 계산합니다.
        """
        self._validate_audio(target_audio, target_sr, "target_audio")
        self._validate_audio(source_audio, source_sr, "source_audio")

        # 특징 추출
        target_features = self._extract_spectral_features(target_audio, target_sr)
        source_features = self._extract_spectral_features(source_audio, source_sr)

        # 각 특징별 유사도 계산
        centroid_sim = self._compute_feature_similarity(
            target_features['centroid'],
            source_features['centroid']
        )

        rolloff_sim = self._compute_feature_similarity(
            target_features['rolloff'],
            source_features['rolloff']
        )

        # 스펙트럼 대비는 다차원이므로 평균 사용
        contrast_sims = []
        for i in range(target_features['contrast'].shape[0]):
            sim = self._compute_feature_similarity(
                target_features['contrast'][i],
                source_features['contrast'][i]
            )
            contrast_sims.append(sim)
        contrast_sim = np.mean(contrast_sims)

        bandwidth_sim = self._compute_feature_similarity(
            target_features['bandwidth'],
            source_features['bandwidth']
        )

        # 가중 평균
        total_similarity = (
            self.centroid_weight * centroid_sim +
            self.rolloff_weight * rolloff_sim +
            self.contrast_weight * contrast_sim +
            self.bandwidth_weight * bandwidth_sim
        )

        return total_similarity

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

        # 타겟 특징 추출
        target_features = self._extract_spectral_features(target_audio, target_sr)

        for i in tqdm(range(num_windows), desc="Searching segments", disable=num_windows < 10):
            start_sample = i * step_samples
            end_sample = start_sample + window_samples

            if end_sample > len(source_audio):
                break

            window_audio = source_audio[start_sample:end_sample]
            window_features = self._extract_spectral_features(window_audio, source_sr)

            # 각 특징별 유사도 계산 및 결합
            centroid_sim = self._compute_feature_similarity(
                target_features['centroid'], window_features['centroid']
            )
            rolloff_sim = self._compute_feature_similarity(
                target_features['rolloff'], window_features['rolloff']
            )

            contrast_sims = []
            min_bands = min(target_features['contrast'].shape[0], window_features['contrast'].shape[0])
            for j in range(min_bands):
                sim = self._compute_feature_similarity(
                    target_features['contrast'][j], window_features['contrast'][j]
                )
                contrast_sims.append(sim)
            contrast_sim = np.mean(contrast_sims) if contrast_sims else 0.0

            bandwidth_sim = self._compute_feature_similarity(
                target_features['bandwidth'], window_features['bandwidth']
            )

            similarity = (
                self.centroid_weight * centroid_sim +
                self.rolloff_weight * rolloff_sim +
                self.contrast_weight * contrast_sim +
                self.bandwidth_weight * bandwidth_sim
            )

            if similarity >= self.similarity_threshold:
                match = SimilarityMatch(
                    target_start=0.0,
                    target_end=target_duration,
                    source_start=start_sample / source_sr,
                    source_end=end_sample / source_sr,
                    similarity=similarity,
                    confidence=1.0,
                    metadata={
                        'centroid_sim': centroid_sim,
                        'rolloff_sim': rolloff_sim,
                        'contrast_sim': contrast_sim,
                        'bandwidth_sim': bandwidth_sim,
                    }
                )
                matches.append(match)

        return self._filter_matches(matches, top_k)


__all__ = ["SpectralSimilarity"]
