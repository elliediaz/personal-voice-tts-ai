"""
Prosody Matching

프로소디(운율) 매칭 모듈
"""

import logging
from typing import Optional

import numpy as np
import librosa
from scipy import interpolate

from core.synthesis.pitch import PitchAdjuster
from core.synthesis.tempo import TempoAdjuster

logger = logging.getLogger(__name__)


class ProsodyMatcher:
    """프로소디 매칭 클래스"""

    def __init__(
        self,
        match_pitch: bool = True,
        match_energy: bool = True,
        match_duration: bool = True,
    ):
        """
        Args:
            match_pitch: 피치 매칭 여부
            match_energy: 에너지 매칭 여부
            match_duration: 길이 매칭 여부
        """
        self.match_pitch = match_pitch
        self.match_energy = match_energy
        self.match_duration = match_duration

        self.pitch_adjuster = PitchAdjuster()
        self.tempo_adjuster = TempoAdjuster()

        logger.info(
            f"ProsodyMatcher 초기화: pitch={match_pitch}, "
            f"energy={match_energy}, duration={match_duration}"
        )

    def match_prosody(
        self,
        source_audio: np.ndarray,
        target_audio: np.ndarray,
        sample_rate: int,
    ) -> np.ndarray:
        """
        타겟의 프로소디에 맞게 소스 조정

        Args:
            source_audio: 소스 오디오
            target_audio: 타겟 오디오 (참조)
            sample_rate: 샘플링 레이트

        Returns:
            프로소디가 조정된 소스 오디오
        """
        adjusted = source_audio.copy()

        # 1. 길이 매칭
        if self.match_duration:
            adjusted = self.tempo_adjuster.match_tempo(
                adjusted, target_audio, sample_rate
            )

        # 2. 피치 매칭
        if self.match_pitch:
            adjusted = self.pitch_adjuster.match_pitch_contour(
                adjusted, target_audio, sample_rate
            )

        # 3. 에너지 매칭
        if self.match_energy:
            adjusted = self._match_energy_envelope(
                adjusted, target_audio, sample_rate
            )

        return adjusted

    def _match_energy_envelope(
        self,
        source_audio: np.ndarray,
        target_audio: np.ndarray,
        sample_rate: int,
    ) -> np.ndarray:
        """
        에너지 엔벨로프 매칭

        Args:
            source_audio: 소스 오디오
            target_audio: 타겟 오디오
            sample_rate: 샘플링 레이트

        Returns:
            에너지가 조정된 오디오
        """
        # RMS 에너지 계산
        frame_length = 2048
        hop_length = 512

        source_rms = librosa.feature.rms(
            y=source_audio, frame_length=frame_length, hop_length=hop_length
        )[0]
        target_rms = librosa.feature.rms(
            y=target_audio, frame_length=frame_length, hop_length=hop_length
        )[0]

        # 길이 맞추기 (interpolation)
        if len(source_rms) != len(target_rms):
            x_old = np.linspace(0, 1, len(target_rms))
            x_new = np.linspace(0, 1, len(source_rms))
            f = interpolate.interp1d(x_old, target_rms, kind="linear", fill_value="extrapolate")
            target_rms_resampled = f(x_new)
        else:
            target_rms_resampled = target_rms

        # 에너지 비율 계산
        eps = 1e-8
        energy_ratio = (target_rms_resampled + eps) / (source_rms + eps)

        # 프레임 단위 에너지 비율을 샘플 단위로 확장
        energy_ratio_full = np.repeat(energy_ratio, hop_length)

        # 길이 맞추기
        if len(energy_ratio_full) > len(source_audio):
            energy_ratio_full = energy_ratio_full[: len(source_audio)]
        elif len(energy_ratio_full) < len(source_audio):
            energy_ratio_full = np.pad(
                energy_ratio_full,
                (0, len(source_audio) - len(energy_ratio_full)),
                mode="edge",
            )

        # 에너지 조정 적용
        adjusted = source_audio * energy_ratio_full

        # 클리핑 방지
        max_val = np.abs(adjusted).max()
        if max_val > 1.0:
            adjusted = adjusted / max_val * 0.99

        return adjusted

    def extract_prosody_features(
        self, audio: np.ndarray, sample_rate: int
    ) -> dict:
        """
        프로소디 특징 추출

        Args:
            audio: 오디오 데이터
            sample_rate: 샘플링 레이트

        Returns:
            프로소디 특징 딕셔너리
        """
        # 피치
        f0, voiced_flag, voiced_probs = librosa.pyin(
            audio,
            fmin=librosa.note_to_hz("C2"),
            fmax=librosa.note_to_hz("C7"),
            sr=sample_rate,
        )

        # 에너지
        rms = librosa.feature.rms(y=audio)[0]

        # 템포
        tempo = self.tempo_adjuster.estimate_tempo(audio, sample_rate)

        # 통계
        valid_f0 = f0[f0 > 0]
        features = {
            "pitch_mean": np.mean(valid_f0) if len(valid_f0) > 0 else 0,
            "pitch_std": np.std(valid_f0) if len(valid_f0) > 0 else 0,
            "pitch_min": np.min(valid_f0) if len(valid_f0) > 0 else 0,
            "pitch_max": np.max(valid_f0) if len(valid_f0) > 0 else 0,
            "energy_mean": np.mean(rms),
            "energy_std": np.std(rms),
            "tempo": tempo,
            "duration": len(audio) / sample_rate,
            "voiced_ratio": np.sum(voiced_flag) / len(voiced_flag),
        }

        return features

    def compare_prosody(
        self,
        audio1: np.ndarray,
        audio2: np.ndarray,
        sample_rate: int,
    ) -> dict:
        """
        두 오디오의 프로소디 비교

        Args:
            audio1: 첫 번째 오디오
            audio2: 두 번째 오디오
            sample_rate: 샘플링 레이트

        Returns:
            비교 결과 딕셔너리
        """
        features1 = self.extract_prosody_features(audio1, sample_rate)
        features2 = self.extract_prosody_features(audio2, sample_rate)

        comparison = {}
        for key in features1.keys():
            val1 = features1[key]
            val2 = features2[key]

            if val2 != 0:
                diff = (val1 - val2) / val2 * 100  # 퍼센트 차이
            else:
                diff = 0

            comparison[key] = {
                "audio1": val1,
                "audio2": val2,
                "difference_percent": diff,
            }

        return comparison

    def __repr__(self) -> str:
        return (
            f"ProsodyMatcher(pitch={self.match_pitch}, "
            f"energy={self.match_energy}, duration={self.match_duration})"
        )
