"""
Audio Blending

오디오 세그먼트를 블렌딩하는 모듈
"""

import logging
from typing import Literal, Optional

import numpy as np
import librosa

logger = logging.getLogger(__name__)


class AudioBlender:
    """오디오 블렌딩 클래스"""

    def __init__(
        self,
        blend_algorithm: Literal[
            "linear", "logarithmic", "equal_power", "spectral"
        ] = "equal_power",
        crossfade_duration: float = 0.05,
    ):
        """
        Args:
            blend_algorithm: 블렌딩 알고리즘
            crossfade_duration: 크로스페이드 길이 (초)
        """
        self.blend_algorithm = blend_algorithm
        self.crossfade_duration = crossfade_duration

        logger.info(
            f"AudioBlender 초기화: algorithm={blend_algorithm}, "
            f"crossfade={crossfade_duration}s"
        )

    def blend_segments(
        self,
        segments: list,
        sample_rate: int,
    ) -> np.ndarray:
        """
        여러 세그먼트를 블렌딩

        Args:
            segments: 오디오 세그먼트 리스트
            sample_rate: 샘플링 레이트

        Returns:
            블렌딩된 오디오
        """
        if not segments:
            raise ValueError("세그먼트가 비어 있습니다")

        if len(segments) == 1:
            return segments[0]

        # 첫 번째 세그먼트로 시작
        result = segments[0].copy()

        # 나머지 세그먼트들을 순차적으로 블렌딩
        for segment in segments[1:]:
            result = self.crossfade(result, segment, sample_rate)

        return result

    def crossfade(
        self,
        audio1: np.ndarray,
        audio2: np.ndarray,
        sample_rate: int,
    ) -> np.ndarray:
        """
        두 오디오를 크로스페이드

        Args:
            audio1: 첫 번째 오디오
            audio2: 두 번째 오디오
            sample_rate: 샘플링 레이트

        Returns:
            크로스페이드된 오디오
        """
        crossfade_samples = int(self.crossfade_duration * sample_rate)

        # 크로스페이드 길이 검증
        crossfade_samples = min(crossfade_samples, len(audio1), len(audio2))

        if crossfade_samples == 0:
            # 크로스페이드 없이 연결
            return np.concatenate([audio1, audio2])

        # 블렌딩 알고리즘에 따라 처리
        if self.blend_algorithm == "linear":
            blended = self._linear_crossfade(audio1, audio2, crossfade_samples)
        elif self.blend_algorithm == "logarithmic":
            blended = self._logarithmic_crossfade(audio1, audio2, crossfade_samples)
        elif self.blend_algorithm == "equal_power":
            blended = self._equal_power_crossfade(audio1, audio2, crossfade_samples)
        elif self.blend_algorithm == "spectral":
            blended = self._spectral_crossfade(
                audio1, audio2, crossfade_samples, sample_rate
            )
        else:
            raise ValueError(f"지원하지 않는 블렌딩 알고리즘: {self.blend_algorithm}")

        return blended

    def _linear_crossfade(
        self, audio1: np.ndarray, audio2: np.ndarray, crossfade_samples: int
    ) -> np.ndarray:
        """선형 크로스페이드"""
        # 크로스페이드 영역
        fade_out = np.linspace(1, 0, crossfade_samples)
        fade_in = np.linspace(0, 1, crossfade_samples)

        # 오디오1의 끝부분과 오디오2의 시작부분 블렌딩
        overlap1 = audio1[-crossfade_samples:] * fade_out
        overlap2 = audio2[:crossfade_samples] * fade_in
        overlapped = overlap1 + overlap2

        # 결과 조합
        result = np.concatenate(
            [audio1[:-crossfade_samples], overlapped, audio2[crossfade_samples:]]
        )

        return result

    def _logarithmic_crossfade(
        self, audio1: np.ndarray, audio2: np.ndarray, crossfade_samples: int
    ) -> np.ndarray:
        """로그 크로스페이드 (더 부드러운 전환)"""
        # 로그 스케일 커브
        t = np.linspace(0, 1, crossfade_samples)
        fade_out = np.log10(1 + 9 * (1 - t))  # 1 -> 0
        fade_in = np.log10(1 + 9 * t)  # 0 -> 1

        # 정규화
        fade_out = fade_out / fade_out[0]
        fade_in = fade_in / fade_in[-1]

        # 블렌딩
        overlap1 = audio1[-crossfade_samples:] * fade_out
        overlap2 = audio2[:crossfade_samples] * fade_in
        overlapped = overlap1 + overlap2

        result = np.concatenate(
            [audio1[:-crossfade_samples], overlapped, audio2[crossfade_samples:]]
        )

        return result

    def _equal_power_crossfade(
        self, audio1: np.ndarray, audio2: np.ndarray, crossfade_samples: int
    ) -> np.ndarray:
        """Equal-power 크로스페이드 (파워 보존)"""
        # Equal-power 커브 (사인/코사인)
        t = np.linspace(0, np.pi / 2, crossfade_samples)
        fade_out = np.cos(t)  # 1 -> 0
        fade_in = np.sin(t)  # 0 -> 1

        # 블렌딩
        overlap1 = audio1[-crossfade_samples:] * fade_out
        overlap2 = audio2[:crossfade_samples] * fade_in
        overlapped = overlap1 + overlap2

        result = np.concatenate(
            [audio1[:-crossfade_samples], overlapped, audio2[crossfade_samples:]]
        )

        return result

    def _spectral_crossfade(
        self,
        audio1: np.ndarray,
        audio2: np.ndarray,
        crossfade_samples: int,
        sample_rate: int,
    ) -> np.ndarray:
        """스펙트럼 영역에서 크로스페이드"""
        # STFT 변환
        n_fft = 2048
        hop_length = 512

        # 크로스페이드 영역 추출
        region1 = audio1[-crossfade_samples:]
        region2 = audio2[:crossfade_samples]

        # STFT
        stft1 = librosa.stft(region1, n_fft=n_fft, hop_length=hop_length)
        stft2 = librosa.stft(region2, n_fft=n_fft, hop_length=hop_length)

        # 선형 보간 (주파수 영역)
        num_frames = min(stft1.shape[1], stft2.shape[1])
        t = np.linspace(0, 1, num_frames)
        fade_out = (1 - t).reshape(1, -1)
        fade_in = t.reshape(1, -1)

        # 블렌딩
        blended_stft = stft1[:, :num_frames] * fade_out + stft2[:, :num_frames] * fade_in

        # ISTFT로 복원
        overlapped = librosa.istft(blended_stft, hop_length=hop_length, length=crossfade_samples)

        # 결과 조합
        result = np.concatenate(
            [audio1[:-crossfade_samples], overlapped, audio2[crossfade_samples:]]
        )

        return result

    def overlap_add(
        self,
        segments: list,
        positions: list,
        total_length: int,
        sample_rate: int,
    ) -> np.ndarray:
        """
        Overlap-add 합성

        Args:
            segments: 세그먼트 리스트
            positions: 각 세그먼트의 위치 (샘플 단위)
            total_length: 전체 길이 (샘플 단위)
            sample_rate: 샘플링 레이트

        Returns:
            합성된 오디오
        """
        result = np.zeros(total_length, dtype=np.float32)

        for segment, pos in zip(segments, positions):
            end_pos = min(pos + len(segment), total_length)
            segment_len = end_pos - pos

            # 겹치는 영역 블렌딩
            if pos < total_length:
                result[pos:end_pos] += segment[:segment_len]

        # 정규화 (클리핑 방지)
        max_val = np.abs(result).max()
        if max_val > 1.0:
            result = result / max_val * 0.99

        return result

    def __repr__(self) -> str:
        return (
            f"AudioBlender(algorithm={self.blend_algorithm}, "
            f"crossfade={self.crossfade_duration}s)"
        )
