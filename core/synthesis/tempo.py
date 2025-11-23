"""
Tempo Adjustment

템포(속도) 조정 모듈
"""

import logging
from typing import Optional

import numpy as np
import librosa

logger = logging.getLogger(__name__)


class TempoAdjuster:
    """템포 조정 클래스"""

    def __init__(
        self,
        preserve_pitch: bool = True,
    ):
        """
        Args:
            preserve_pitch: 피치 보존 여부
        """
        self.preserve_pitch = preserve_pitch

        logger.info(f"TempoAdjuster 초기화: preserve_pitch={preserve_pitch}")

    def adjust_tempo(
        self,
        audio: np.ndarray,
        sample_rate: int,
        rate: float,
    ) -> np.ndarray:
        """
        템포 조정

        Args:
            audio: 오디오 데이터
            sample_rate: 샘플링 레이트
            rate: 속도 비율 (1.0=원본, >1.0=빠르게, <1.0=느리게)

        Returns:
            템포가 조정된 오디오
        """
        if abs(rate - 1.0) < 0.01:
            # 변화가 거의 없으면 원본 반환
            return audio

        logger.debug(f"템포 조정: rate={rate:.2f}x")

        if self.preserve_pitch:
            # 피치 보존하며 템포 조정
            adjusted = librosa.effects.time_stretch(audio, rate=rate)
        else:
            # 리샘플링으로 템포 조정 (피치도 변경됨)
            adjusted = librosa.resample(
                audio, orig_sr=sample_rate, target_sr=int(sample_rate * rate)
            )

        return adjusted

    def match_duration(
        self,
        audio: np.ndarray,
        target_duration: float,
        sample_rate: int,
    ) -> np.ndarray:
        """
        타겟 길이에 맞게 조정

        Args:
            audio: 오디오 데이터
            target_duration: 타겟 길이 (초)
            sample_rate: 샘플링 레이트

        Returns:
            길이가 조정된 오디오
        """
        current_duration = len(audio) / sample_rate
        rate = current_duration / target_duration

        logger.debug(
            f"길이 매칭: {current_duration:.2f}s -> {target_duration:.2f}s "
            f"(rate={rate:.2f}x)"
        )

        return self.adjust_tempo(audio, sample_rate, rate)

    def match_tempo(
        self,
        source_audio: np.ndarray,
        target_audio: np.ndarray,
        sample_rate: int,
    ) -> np.ndarray:
        """
        타겟의 템포에 맞게 소스 조정

        Args:
            source_audio: 소스 오디오
            target_audio: 타겟 오디오 (참조)
            sample_rate: 샘플링 레이트

        Returns:
            템포가 조정된 소스 오디오
        """
        # 길이 비율 계산
        source_duration = len(source_audio) / sample_rate
        target_duration = len(target_audio) / sample_rate

        # 템포 조정
        adjusted = self.match_duration(source_audio, target_duration, sample_rate)

        return adjusted

    def estimate_tempo(self, audio: np.ndarray, sample_rate: int) -> float:
        """
        템포 추정 (BPM)

        Args:
            audio: 오디오 데이터
            sample_rate: 샘플링 레이트

        Returns:
            추정된 BPM
        """
        # Onset strength 계산
        onset_env = librosa.onset.onset_strength(y=audio, sr=sample_rate)

        # Tempogram 기반 템포 추정
        tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sample_rate)[0]

        logger.debug(f"템포 추정: {tempo:.1f} BPM")

        return float(tempo)

    def detect_beats(
        self, audio: np.ndarray, sample_rate: int
    ) -> tuple:
        """
        비트 검출

        Args:
            audio: 오디오 데이터
            sample_rate: 샘플링 레이트

        Returns:
            (tempo, beat_frames) 튜플
        """
        # 비트 트래킹
        tempo, beat_frames = librosa.beat.beat_track(y=audio, sr=sample_rate)

        # 프레임을 시간으로 변환
        beat_times = librosa.frames_to_time(beat_frames, sr=sample_rate)

        logger.debug(f"비트 검출: {len(beat_frames)}개 비트, {tempo:.1f} BPM")

        return tempo, beat_times

    def __repr__(self) -> str:
        return f"TempoAdjuster(preserve_pitch={self.preserve_pitch})"
