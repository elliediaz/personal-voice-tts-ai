"""
MFCC-based Similarity Algorithm

MFCC (Mel-Frequency Cepstral Coefficients) 특징을 사용한 유사도 검출 알고리즘입니다.
"""

from typing import List, Optional
import numpy as np
import librosa
from scipy.spatial.distance import euclidean, cosine
from scipy.signal import correlate
from tqdm import tqdm

from algorithms.base import BaseSimilarityAlgorithm, SimilarityMatch
from utils.logging import get_logger

logger = get_logger(__name__)


class MFCCSimilarity(BaseSimilarityAlgorithm):
    """
    MFCC 기반 유사도 알고리즘.

    MFCC 특징을 추출하여 타겟과 소스 오디오 간의 유사도를 계산합니다.
    """

    def __init__(
        self,
        n_mfcc: int = 13,
        n_fft: int = 2048,
        hop_length: int = 512,
        window: str = 'hann',
        distance_metric: str = 'euclidean',
        use_dtw: bool = False,
        use_delta: bool = False,
        use_delta_delta: bool = False,
        **kwargs
    ):
        """
        MFCCSimilarity를 초기화합니다.

        Args:
            n_mfcc: MFCC 계수 개수
            n_fft: FFT 윈도우 크기
            hop_length: 홉 길이
            window: 윈도우 함수
            distance_metric: 거리 메트릭 ('euclidean', 'cosine', 'correlation')
            use_dtw: DTW (Dynamic Time Warping) 사용 여부
            use_delta: Delta MFCC 사용 여부
            use_delta_delta: Delta-Delta MFCC 사용 여부
            **kwargs: 기본 클래스 파라미터
        """
        super().__init__(**kwargs)

        self.n_mfcc = n_mfcc
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.window = window
        self.distance_metric = distance_metric
        self.use_dtw = use_dtw
        self.use_delta = use_delta
        self.use_delta_delta = use_delta_delta

        logger.info(
            f"MFCCSimilarity 초기화: n_mfcc={n_mfcc}, "
            f"distance_metric={distance_metric}, use_dtw={use_dtw}"
        )

    def _extract_mfcc(
        self,
        audio: np.ndarray,
        sr: int,
    ) -> np.ndarray:
        """
        오디오로부터 MFCC 특징을 추출합니다.

        Args:
            audio: 오디오 데이터
            sr: 샘플링 레이트

        Returns:
            np.ndarray: MFCC 특징 (shape: (n_features, n_frames))
        """
        # MFCC 추출
        mfcc = librosa.feature.mfcc(
            y=audio,
            sr=sr,
            n_mfcc=self.n_mfcc,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
            window=self.window,
        )

        features = [mfcc]

        # Delta MFCC 추가
        if self.use_delta:
            delta = librosa.feature.delta(mfcc)
            features.append(delta)

        # Delta-Delta MFCC 추가
        if self.use_delta_delta:
            delta2 = librosa.feature.delta(mfcc, order=2)
            features.append(delta2)

        # 모든 특징 결합
        combined_features = np.vstack(features)

        return combined_features

    def _compute_distance(
        self,
        feat1: np.ndarray,
        feat2: np.ndarray,
    ) -> float:
        """
        두 MFCC 특징 간의 거리를 계산합니다.

        Args:
            feat1: 첫 번째 MFCC 특징
            feat2: 두 번째 MFCC 특징

        Returns:
            float: 거리 값
        """
        if self.use_dtw:
            # DTW 거리 사용
            distance = self._dtw_distance(feat1, feat2)
        else:
            # 프레임별 평균 거리
            min_frames = min(feat1.shape[1], feat2.shape[1])
            feat1_trimmed = feat1[:, :min_frames]
            feat2_trimmed = feat2[:, :min_frames]

            if self.distance_metric == 'euclidean':
                # 유클리드 거리
                distance = np.mean([
                    euclidean(feat1_trimmed[:, i], feat2_trimmed[:, i])
                    for i in range(min_frames)
                ])
            elif self.distance_metric == 'cosine':
                # 코사인 거리
                distance = np.mean([
                    cosine(feat1_trimmed[:, i], feat2_trimmed[:, i])
                    for i in range(min_frames)
                ])
            elif self.distance_metric == 'correlation':
                # 상관 계수 기반 거리
                correlations = []
                for i in range(feat1.shape[0]):
                    corr = np.corrcoef(feat1_trimmed[i, :], feat2_trimmed[i, :])[0, 1]
                    correlations.append(1 - abs(corr))  # 1 - |correlation|
                distance = np.mean(correlations)
            else:
                raise ValueError(f"지원하지 않는 거리 메트릭: {self.distance_metric}")

        return distance

    def _dtw_distance(
        self,
        feat1: np.ndarray,
        feat2: np.ndarray,
    ) -> float:
        """
        DTW (Dynamic Time Warping) 거리를 계산합니다.

        Args:
            feat1: 첫 번째 MFCC 특징
            feat2: 두 번째 MFCC 특징

        Returns:
            float: DTW 거리
        """
        n, m = feat1.shape[1], feat2.shape[1]

        # DTW 행렬 초기화
        dtw_matrix = np.zeros((n + 1, m + 1))
        dtw_matrix[0, :] = np.inf
        dtw_matrix[:, 0] = np.inf
        dtw_matrix[0, 0] = 0

        # DTW 계산
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                cost = euclidean(feat1[:, i - 1], feat2[:, j - 1])
                dtw_matrix[i, j] = cost + min(
                    dtw_matrix[i - 1, j],      # insertion
                    dtw_matrix[i, j - 1],      # deletion
                    dtw_matrix[i - 1, j - 1],  # match
                )

        return dtw_matrix[n, m] / (n + m)  # Normalize by path length

    def compute_similarity(
        self,
        target_audio: np.ndarray,
        source_audio: np.ndarray,
        target_sr: int,
        source_sr: int,
    ) -> float:
        """
        두 오디오 간의 MFCC 기반 유사도를 계산합니다.

        Args:
            target_audio: 타겟 오디오 데이터
            source_audio: 소스 오디오 데이터
            target_sr: 타겟 샘플링 레이트
            source_sr: 소스 샘플링 레이트

        Returns:
            float: 유사도 점수 (0.0 ~ 1.0, 높을수록 유사)
        """
        self._validate_audio(target_audio, target_sr, "target_audio")
        self._validate_audio(source_audio, source_sr, "source_audio")

        logger.debug("MFCC 특징 추출 중...")

        # MFCC 추출
        target_mfcc = self._extract_mfcc(target_audio, target_sr)
        source_mfcc = self._extract_mfcc(source_audio, source_sr)

        # 거리 계산
        distance = self._compute_distance(target_mfcc, source_mfcc)

        # 거리를 유사도로 변환 (0 ~ 1, 높을수록 유사)
        # 거리가 0이면 유사도 1, 거리가 클수록 유사도 감소
        similarity = 1.0 / (1.0 + distance)

        logger.debug(f"유사도 계산 완료: {similarity:.3f} (거리: {distance:.3f})")

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

        슬라이딩 윈도우를 사용하여 소스 오디오에서 타겟과 유사한 구간을 검색합니다.

        Args:
            target_audio: 타겟 오디오 데이터
            source_audio: 소스 오디오 데이터
            target_sr: 타겟 샘플링 레이트
            source_sr: 소스 샘플링 레이트
            top_k: 반환할 최대 매치 수

        Returns:
            List[SimilarityMatch]: 유사 세그먼트 리스트
        """
        self._validate_audio(target_audio, target_sr, "target_audio")
        self._validate_audio(source_audio, source_sr, "source_audio")

        logger.info("유사 세그먼트 검색 시작...")

        # 타겟 오디오 전체의 MFCC 추출
        target_mfcc = self._extract_mfcc(target_audio, target_sr)
        target_duration = len(target_audio) / target_sr

        # 타겟 길이와 유사한 윈도우 크기 설정
        window_duration = min(target_duration, self.segment_max_length)
        window_duration = max(window_duration, self.segment_min_length)
        window_samples = int(window_duration * source_sr)

        # 슬라이딩 윈도우 스텝 (50% 오버랩)
        step_samples = window_samples // 2

        matches = []

        # 슬라이딩 윈도우로 소스 오디오 탐색
        num_windows = (len(source_audio) - window_samples) // step_samples + 1

        for i in tqdm(range(num_windows), desc="Searching segments", disable=num_windows < 10):
            start_sample = i * step_samples
            end_sample = start_sample + window_samples

            if end_sample > len(source_audio):
                break

            # 현재 윈도우 추출
            window_audio = source_audio[start_sample:end_sample]

            # MFCC 추출
            window_mfcc = self._extract_mfcc(window_audio, source_sr)

            # 유사도 계산
            distance = self._compute_distance(target_mfcc, window_mfcc)
            similarity = 1.0 / (1.0 + distance)

            # 매치 생성
            if similarity >= self.similarity_threshold:
                match = SimilarityMatch(
                    target_start=0.0,
                    target_end=target_duration,
                    source_start=start_sample / source_sr,
                    source_end=end_sample / source_sr,
                    similarity=similarity,
                    confidence=1.0,
                    metadata={
                        'distance': distance,
                        'distance_metric': self.distance_metric,
                        'use_dtw': self.use_dtw,
                    }
                )
                matches.append(match)

        # 필터링 및 정렬
        filtered_matches = self._filter_matches(matches, top_k)

        logger.info(f"유사 세그먼트 검색 완료: {len(filtered_matches)}개 발견")

        return filtered_matches


__all__ = ["MFCCSimilarity"]
