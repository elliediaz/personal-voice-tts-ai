"""
Pitch Adjustment

피치(음고) 조정 모듈
"""

import logging
from typing import Literal, Optional

import numpy as np
import librosa

logger = logging.getLogger(__name__)


class PitchAdjuster:
    """피치 조정 클래스"""

    def __init__(
        self,
        method: Literal["phase_vocoder", "time_stretch"] = "phase_vocoder",
        preserve_formants: bool = True,
    ):
        """
        Args:
            method: 피치 조정 방법
            preserve_formants: 포먼트 보존 여부
        """
        self.method = method
        self.preserve_formants = preserve_formants

        logger.info(
            f"PitchAdjuster 초기화: method={method}, "
            f"preserve_formants={preserve_formants}"
        )

    def adjust_pitch(
        self,
        audio: np.ndarray,
        sample_rate: int,
        n_steps: float,
    ) -> np.ndarray:
        """
        피치 조정

        Args:
            audio: 오디오 데이터
            sample_rate: 샘플링 레이트
            n_steps: 반음 단위 피치 변화 (양수=높게, 음수=낮게)

        Returns:
            피치가 조정된 오디오
        """
        if abs(n_steps) < 0.01:
            # 변화가 거의 없으면 원본 반환
            return audio

        logger.debug(f"피치 조정: {n_steps:+.2f} 반음")

        if self.method == "phase_vocoder":
            return self._phase_vocoder_pitch_shift(audio, sample_rate, n_steps)
        elif self.method == "time_stretch":
            return self._time_stretch_pitch_shift(audio, sample_rate, n_steps)
        else:
            raise ValueError(f"지원하지 않는 피치 조정 방법: {self.method}")

    def _phase_vocoder_pitch_shift(
        self, audio: np.ndarray, sample_rate: int, n_steps: float
    ) -> np.ndarray:
        """Phase vocoder를 사용한 피치 조정"""
        # librosa.effects.pitch_shift 사용
        shifted = librosa.effects.pitch_shift(
            audio, sr=sample_rate, n_steps=n_steps
        )

        return shifted

    def _time_stretch_pitch_shift(
        self, audio: np.ndarray, sample_rate: int, n_steps: float
    ) -> np.ndarray:
        """Time stretching을 사용한 피치 조정"""
        # 피치 변화 = 시간 변화 + 리샘플링
        # 1. 시간 축소/확장
        rate = 2 ** (n_steps / 12.0)  # 반음당 2^(1/12)
        stretched = librosa.effects.time_stretch(audio, rate=rate)

        # 2. 리샘플링으로 길이 보정
        target_length = len(audio)
        if len(stretched) != target_length:
            stretched = librosa.resample(
                stretched,
                orig_sr=sample_rate,
                target_sr=int(sample_rate / rate),
            )
            # 길이 맞추기
            if len(stretched) > target_length:
                stretched = stretched[:target_length]
            elif len(stretched) < target_length:
                stretched = np.pad(
                    stretched, (0, target_length - len(stretched)), mode="constant"
                )

        return stretched

    def match_pitch_contour(
        self,
        source_audio: np.ndarray,
        target_audio: np.ndarray,
        sample_rate: int,
    ) -> np.ndarray:
        """
        타겟의 피치 윤곽에 맞게 소스 조정

        Args:
            source_audio: 소스 오디오
            target_audio: 타겟 오디오 (참조)
            sample_rate: 샘플링 레이트

        Returns:
            피치가 조정된 소스 오디오
        """
        # 피치 추출
        source_f0, _, _ = self._extract_pitch(source_audio, sample_rate)
        target_f0, _, _ = self._extract_pitch(target_audio, sample_rate)

        # 평균 피치 비율 계산
        source_f0_mean = np.nanmean(source_f0[source_f0 > 0])
        target_f0_mean = np.nanmean(target_f0[target_f0 > 0])

        if np.isnan(source_f0_mean) or np.isnan(target_f0_mean):
            logger.warning("피치 추출 실패, 원본 반환")
            return source_audio

        # 반음 단위로 변환
        ratio = target_f0_mean / source_f0_mean
        n_steps = 12 * np.log2(ratio)

        logger.debug(
            f"피치 매칭: source={source_f0_mean:.1f}Hz, "
            f"target={target_f0_mean:.1f}Hz, shift={n_steps:+.2f}반음"
        )

        # 피치 조정
        adjusted = self.adjust_pitch(source_audio, sample_rate, n_steps)

        return adjusted

    def _extract_pitch(
        self, audio: np.ndarray, sample_rate: int
    ) -> tuple:
        """
        피치 추출 (F0)

        Returns:
            (f0, voiced_flag, voiced_probs) 튜플
        """
        # librosa.pyin 사용 (더 정확한 피치 추출)
        f0, voiced_flag, voiced_probs = librosa.pyin(
            audio,
            fmin=librosa.note_to_hz("C2"),  # 약 65Hz
            fmax=librosa.note_to_hz("C7"),  # 약 2093Hz
            sr=sample_rate,
        )

        return f0, voiced_flag, voiced_probs

    def estimate_pitch_range(
        self, audio: np.ndarray, sample_rate: int
    ) -> tuple:
        """
        피치 범위 추정

        Returns:
            (min_pitch, max_pitch, mean_pitch) 튜플 (Hz 단위)
        """
        f0, _, _ = self._extract_pitch(audio, sample_rate)

        # 유효한 피치만 선택
        valid_f0 = f0[f0 > 0]

        if len(valid_f0) == 0:
            return (0, 0, 0)

        min_pitch = np.min(valid_f0)
        max_pitch = np.max(valid_f0)
        mean_pitch = np.mean(valid_f0)

        return (min_pitch, max_pitch, mean_pitch)

    def __repr__(self) -> str:
        return f"PitchAdjuster(method={self.method})"
