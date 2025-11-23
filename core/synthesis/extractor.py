"""
Segment Extractor

오디오 파일에서 세그먼트를 추출하는 모듈
"""

import logging
from typing import Optional, Tuple
from pathlib import Path

import numpy as np
import librosa

from algorithms.base import SimilarityMatch
from core.audio.io import AudioFile

logger = logging.getLogger(__name__)


class SegmentExtractor:
    """오디오 세그먼트 추출 클래스"""

    def __init__(
        self,
        fade_duration: float = 0.01,
        min_segment_length: float = 0.1,
        normalize: bool = True,
    ):
        """
        Args:
            fade_duration: 페이드 인/아웃 길이 (초)
            min_segment_length: 최소 세그먼트 길이 (초)
            normalize: 세그먼트 정규화 여부
        """
        self.fade_duration = fade_duration
        self.min_segment_length = min_segment_length
        self.normalize = normalize

        logger.info(
            f"SegmentExtractor 초기화: fade={fade_duration}s, "
            f"min_length={min_segment_length}s"
        )

    def extract_from_match(
        self,
        source_audio: np.ndarray,
        source_sr: int,
        match: SimilarityMatch,
    ) -> Tuple[np.ndarray, int]:
        """
        SimilarityMatch로부터 세그먼트 추출

        Args:
            source_audio: 소스 오디오 데이터
            source_sr: 소스 샘플링 레이트
            match: 유사도 매치 정보

        Returns:
            (추출된 세그먼트, 샘플링 레이트) 튜플
        """
        start_time = match.source_start
        end_time = match.source_end

        return self.extract(source_audio, source_sr, start_time, end_time)

    def extract(
        self,
        audio: np.ndarray,
        sample_rate: int,
        start_time: float,
        end_time: float,
    ) -> Tuple[np.ndarray, int]:
        """
        시간 범위로부터 세그먼트 추출

        Args:
            audio: 오디오 데이터
            sample_rate: 샘플링 레이트
            start_time: 시작 시간 (초)
            end_time: 종료 시간 (초)

        Returns:
            (추출된 세그먼트, 샘플링 레이트) 튜플
        """
        # 시간을 샘플 인덱스로 변환
        start_sample = int(start_time * sample_rate)
        end_sample = int(end_time * sample_rate)

        # 경계 검증
        start_sample = max(0, start_sample)
        end_sample = min(len(audio), end_sample)

        # 세그먼트 길이 검증
        duration = (end_sample - start_sample) / sample_rate
        if duration < self.min_segment_length:
            logger.warning(
                f"세그먼트가 너무 짧습니다: {duration:.3f}s < {self.min_segment_length}s"
            )
            # 최소 길이만큼 확장
            needed_samples = int(self.min_segment_length * sample_rate)
            if end_sample - start_sample < needed_samples:
                # 가능하면 양쪽으로 확장
                diff = needed_samples - (end_sample - start_sample)
                start_sample = max(0, start_sample - diff // 2)
                end_sample = min(len(audio), start_sample + needed_samples)

        # 세그먼트 추출
        segment = audio[start_sample:end_sample].copy()

        # 페이드 인/아웃 적용
        segment = self._apply_fade(segment, sample_rate)

        # 정규화 (옵션)
        if self.normalize:
            segment = self._normalize_segment(segment)

        logger.debug(
            f"세그먼트 추출: {start_time:.2f}s ~ {end_time:.2f}s "
            f"({len(segment)} 샘플)"
        )

        return segment, sample_rate

    def extract_from_file(
        self,
        file_path: Path,
        start_time: float,
        end_time: float,
    ) -> Tuple[np.ndarray, int]:
        """
        파일에서 직접 세그먼트 추출

        Args:
            file_path: 오디오 파일 경로
            start_time: 시작 시간 (초)
            end_time: 종료 시간 (초)

        Returns:
            (추출된 세그먼트, 샘플링 레이트) 튜플
        """
        # 오디오 파일 로드
        audio_file = AudioFile.load(file_path)

        return self.extract(
            audio_file.data, audio_file.sample_rate, start_time, end_time
        )

    def _apply_fade(self, segment: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        페이드 인/아웃 적용

        Args:
            segment: 오디오 세그먼트
            sample_rate: 샘플링 레이트

        Returns:
            페이드가 적용된 세그먼트
        """
        fade_samples = int(self.fade_duration * sample_rate)

        # 세그먼트가 페이드보다 짧으면 스킵
        if len(segment) < fade_samples * 2:
            return segment

        # 페이드 인 (선형)
        fade_in = np.linspace(0, 1, fade_samples, dtype=segment.dtype)
        segment[:fade_samples] *= fade_in

        # 페이드 아웃 (선형)
        fade_out = np.linspace(1, 0, fade_samples, dtype=segment.dtype)
        segment[-fade_samples:] *= fade_out

        return segment

    def _normalize_segment(self, segment: np.ndarray) -> np.ndarray:
        """
        세그먼트 정규화

        Args:
            segment: 오디오 세그먼트

        Returns:
            정규화된 세그먼트
        """
        # RMS 정규화
        rms = np.sqrt(np.mean(segment**2))
        if rms > 0:
            target_rms = 0.1  # 타겟 RMS 레벨
            segment = segment * (target_rms / rms)

        # 클리핑 방지
        max_val = np.abs(segment).max()
        if max_val > 1.0:
            segment = segment / max_val * 0.99

        return segment

    def validate_segment(self, segment: np.ndarray, sample_rate: int) -> bool:
        """
        세그먼트 유효성 검증

        Args:
            segment: 오디오 세그먼트
            sample_rate: 샘플링 레이트

        Returns:
            유효하면 True
        """
        # 길이 검증
        duration = len(segment) / sample_rate
        if duration < self.min_segment_length:
            logger.warning(f"세그먼트가 너무 짧습니다: {duration:.3f}s")
            return False

        # 무음 검증
        rms = np.sqrt(np.mean(segment**2))
        if rms < 1e-6:
            logger.warning("세그먼트가 거의 무음입니다")
            return False

        # 클리핑 검증
        if np.abs(segment).max() > 1.0:
            logger.warning("세그먼트에 클리핑이 있습니다")
            return False

        return True

    def __repr__(self) -> str:
        return (
            f"SegmentExtractor(fade={self.fade_duration}s, "
            f"min_length={self.min_segment_length}s)"
        )
