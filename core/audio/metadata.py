"""
Audio Metadata Module

오디오 파일의 메타데이터를 추출하고 관리합니다.
"""

import hashlib
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Optional, Any
import json

import numpy as np
import librosa

from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class AudioMetadata:
    """
    오디오 메타데이터를 저장하는 데이터 클래스.

    Attributes:
        file_path: 파일 경로
        file_name: 파일 이름
        file_size: 파일 크기 (bytes)
        format: 파일 포맷
        sample_rate: 샘플링 레이트 (Hz)
        channels: 채널 수
        duration: 길이 (초)
        num_samples: 총 샘플 수
        bit_depth: 비트 깊이
        fingerprint: 오디오 지문 (MD5 해시)
        statistics: 통계 정보 (평균, 최대, 최소 등)
    """

    file_path: str
    file_name: str
    file_size: int
    format: str
    sample_rate: int
    channels: int
    duration: float
    num_samples: int
    bit_depth: Optional[int] = None
    fingerprint: Optional[str] = None
    statistics: Optional[Dict[str, float]] = None

    @classmethod
    def from_audio_file(
        cls,
        file_path: Path,
        audio_data: np.ndarray,
        sample_rate: int,
        compute_fingerprint: bool = True,
        compute_statistics: bool = True,
    ) -> "AudioMetadata":
        """
        오디오 파일로부터 메타데이터를 생성합니다.

        Args:
            file_path: 파일 경로
            audio_data: 오디오 데이터
            sample_rate: 샘플링 레이트
            compute_fingerprint: 지문 계산 여부
            compute_statistics: 통계 계산 여부

        Returns:
            AudioMetadata: 메타데이터 객체
        """
        logger.debug(f"메타데이터 추출 중: {file_path}")

        # 기본 정보
        file_stat = file_path.stat()
        file_name = file_path.name
        file_size = file_stat.st_size
        format = file_path.suffix.lstrip('.').lower()

        # 오디오 정보
        if audio_data.ndim == 1:
            channels = 1
            num_samples = len(audio_data)
        else:
            channels = audio_data.shape[1] if audio_data.shape[1] < audio_data.shape[0] else audio_data.shape[0]
            num_samples = len(audio_data)

        duration = num_samples / sample_rate

        # 지문 계산 (옵션)
        fingerprint = None
        if compute_fingerprint:
            fingerprint = cls._compute_fingerprint(audio_data)

        # 통계 계산 (옵션)
        statistics = None
        if compute_statistics:
            statistics = cls._compute_statistics(audio_data)

        return cls(
            file_path=str(file_path),
            file_name=file_name,
            file_size=file_size,
            format=format,
            sample_rate=sample_rate,
            channels=channels,
            duration=duration,
            num_samples=num_samples,
            fingerprint=fingerprint,
            statistics=statistics,
        )

    @staticmethod
    def _compute_fingerprint(audio_data: np.ndarray) -> str:
        """
        오디오 데이터의 MD5 지문을 계산합니다.

        Args:
            audio_data: 오디오 데이터

        Returns:
            str: MD5 해시 문자열
        """
        # 데이터를 bytes로 변환하여 해시 계산
        audio_bytes = audio_data.tobytes()
        fingerprint = hashlib.md5(audio_bytes).hexdigest()

        logger.debug(f"오디오 지문 계산 완료: {fingerprint}")

        return fingerprint

    @staticmethod
    def _compute_statistics(audio_data: np.ndarray) -> Dict[str, float]:
        """
        오디오 데이터의 통계 정보를 계산합니다.

        Args:
            audio_data: 오디오 데이터

        Returns:
            Dict[str, float]: 통계 정보
        """
        statistics = {
            'mean': float(np.mean(audio_data)),
            'std': float(np.std(audio_data)),
            'min': float(np.min(audio_data)),
            'max': float(np.max(audio_data)),
            'median': float(np.median(audio_data)),
            'rms': float(np.sqrt(np.mean(audio_data ** 2))),
        }

        logger.debug(f"통계 정보 계산 완료: RMS={statistics['rms']:.4f}")

        return statistics

    def to_dict(self) -> Dict[str, Any]:
        """
        메타데이터를 딕셔너리로 변환합니다.

        Returns:
            Dict[str, Any]: 메타데이터 딕셔너리
        """
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """
        메타데이터를 JSON 문자열로 변환합니다.

        Args:
            indent: 들여쓰기 크기

        Returns:
            str: JSON 문자열
        """
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def save(self, output_path: Path) -> None:
        """
        메타데이터를 JSON 파일로 저장합니다.

        Args:
            output_path: 저장할 파일 경로
        """
        logger.info(f"메타데이터 저장 중: {output_path}")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(self.to_json())

        logger.info("메타데이터 저장 완료")

    @classmethod
    def load(cls, input_path: Path) -> "AudioMetadata":
        """
        JSON 파일로부터 메타데이터를 로드합니다.

        Args:
            input_path: 메타데이터 파일 경로

        Returns:
            AudioMetadata: 메타데이터 객체
        """
        logger.info(f"메타데이터 로딩 중: {input_path}")

        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return cls(**data)

    def __repr__(self) -> str:
        """문자열 표현"""
        return (
            f"AudioMetadata(\n"
            f"  file_name={self.file_name},\n"
            f"  format={self.format},\n"
            f"  sample_rate={self.sample_rate}Hz,\n"
            f"  channels={self.channels},\n"
            f"  duration={self.duration:.2f}s,\n"
            f"  file_size={self.file_size:,} bytes\n"
            f")"
        )


__all__ = ["AudioMetadata"]
