"""
Audio I/O Module

오디오 파일 로딩, 저장 및 기본 조작 기능을 제공합니다.
"""

import warnings
from pathlib import Path
from typing import Optional, Tuple, Union

import librosa
import numpy as np
import soundfile as sf

# pydub는 선택적 의존성 (MP3/M4A/AAC 저장 시에만 필요)
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    AudioSegment = None

from config import get_config
from utils.logging import get_logger
from utils.validators import validate_audio_file, validate_output_path, validate_sample_rate, validate_channels

logger = get_logger(__name__)

# pydub 미설치 시 경고 로깅
if not PYDUB_AVAILABLE:
    logger.warning("pydub 미설치: MP3/M4A/AAC 저장 기능이 제한됩니다 (WAV로 대체됨)")


class AudioFile:
    """
    오디오 파일을 표현하는 클래스.

    이 클래스는 다양한 형식의 오디오 파일을 로드하고 저장하며,
    기본적인 메타데이터를 제공합니다.

    Attributes:
        data: 오디오 데이터 (numpy 배열, shape: (channels, samples) 또는 (samples,))
        sample_rate: 샘플링 레이트 (Hz)
        channels: 채널 수
        duration: 오디오 길이 (초)
        file_path: 원본 파일 경로
    """

    def __init__(
        self,
        data: np.ndarray,
        sample_rate: int,
        file_path: Optional[Union[str, Path]] = None,
    ):
        """
        AudioFile 인스턴스를 초기화합니다.

        Args:
            data: 오디오 데이터
            sample_rate: 샘플링 레이트
            file_path: 파일 경로 (선택사항)
        """
        self.data = data
        self.sample_rate = validate_sample_rate(sample_rate)
        self.file_path = Path(file_path) if file_path else None

        # 채널 수 확인
        if data.ndim == 1:
            self.channels = 1
            self.data = data
        elif data.ndim == 2:
            # librosa는 (samples, channels), soundfile은 (samples, channels) 또는 (channels, samples)
            # 일관성을 위해 (samples,) 또는 (samples, channels) 형태로 통일
            if data.shape[0] < data.shape[1]:
                # (channels, samples) -> (samples, channels)
                self.data = data.T
            self.channels = self.data.shape[1] if self.data.ndim > 1 else 1
        else:
            raise ValueError(f"지원하지 않는 오디오 데이터 shape입니다: {data.shape}")

        validate_channels(self.channels)

    @property
    def duration(self) -> float:
        """
        오디오 길이를 초 단위로 반환합니다.

        Returns:
            float: 오디오 길이 (초)
        """
        return len(self.data) / self.sample_rate

    @property
    def num_samples(self) -> int:
        """
        총 샘플 수를 반환합니다.

        Returns:
            int: 샘플 수
        """
        return len(self.data)

    @classmethod
    def load(
        cls,
        file_path: Union[str, Path],
        sample_rate: Optional[int] = None,
        mono: bool = False,
        offset: float = 0.0,
        duration: Optional[float] = None,
    ) -> "AudioFile":
        """
        오디오 파일을 로드합니다.

        Args:
            file_path: 로드할 오디오 파일의 경로
            sample_rate: 목표 샘플링 레이트 (None인 경우 원본 사용)
            mono: True인 경우 모노로 변환
            offset: 시작 위치 (초)
            duration: 로드할 길이 (초, None인 경우 전체)

        Returns:
            AudioFile: 로드된 오디오 객체

        Raises:
            FileNotFoundError: 파일이 존재하지 않을 때
            ValueError: 지원하지 않는 파일 형식일 때
        """
        config = get_config()
        file_path = validate_audio_file(file_path, config.audio.supported_formats)

        logger.info(f"오디오 파일 로딩 시작: {file_path}")

        try:
            # librosa를 사용하여 로드
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                data, sr = librosa.load(
                    str(file_path),
                    sr=sample_rate,
                    mono=mono,
                    offset=offset,
                    duration=duration,
                )

            logger.info(
                f"오디오 파일 로딩 완료: "
                f"샘플레이트={sr}Hz, 채널={1 if mono or data.ndim == 1 else data.shape[0]}, "
                f"길이={len(data)/sr:.2f}초"
            )

            return cls(data, sr, file_path)

        except Exception as e:
            logger.error(f"오디오 파일 로딩 실패: {file_path} - {str(e)}")
            raise

    def save(
        self,
        output_path: Union[str, Path],
        format: Optional[str] = None,
        bitrate: str = "320k",
        **kwargs
    ) -> Path:
        """
        오디오를 파일로 저장합니다.

        Args:
            output_path: 저장할 파일 경로
            format: 저장 포맷 (None인 경우 확장자에서 추론)
            bitrate: MP3 등의 비트레이트
            **kwargs: soundfile 또는 pydub의 추가 인자

        Returns:
            Path: 저장된 파일 경로

        Raises:
            ValueError: 지원하지 않는 포맷일 때
        """
        output_path = validate_output_path(output_path)

        # 포맷 결정
        if format is None:
            format = output_path.suffix.lstrip('.').lower()

        logger.info(f"오디오 파일 저장 시작: {output_path} (포맷: {format})")

        try:
            if format in ['wav', 'flac', 'ogg']:
                # soundfile을 사용하여 무손실 포맷 저장
                sf.write(str(output_path), self.data, self.sample_rate, **kwargs)
            elif format in ['mp3', 'm4a', 'aac']:
                # pydub를 사용하여 손실 압축 포맷 저장
                if not PYDUB_AVAILABLE:
                    # pydub 미설치 시 WAV로 대체 저장
                    wav_path = output_path.with_suffix('.wav')
                    sf.write(str(wav_path), self.data, self.sample_rate)
                    logger.warning(
                        f"pydub 미설치로 {format.upper()} 대신 WAV로 저장됨: {wav_path}"
                    )
                    return wav_path
                # numpy 배열을 pydub AudioSegment로 변환
                audio_segment = self._to_audio_segment()
                audio_segment.export(
                    str(output_path),
                    format=format,
                    bitrate=bitrate,
                    **kwargs
                )
            else:
                raise ValueError(f"지원하지 않는 저장 포맷입니다: {format}")

            logger.info(f"오디오 파일 저장 완료: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"오디오 파일 저장 실패: {output_path} - {str(e)}")
            raise

    def _to_audio_segment(self) -> AudioSegment:
        """
        numpy 배열을 pydub AudioSegment로 변환합니다.

        Returns:
            AudioSegment: 변환된 오디오 세그먼트
        """
        # float32 -> int16 변환
        audio_int16 = (self.data * 32767).astype(np.int16)

        # bytes로 변환
        audio_bytes = audio_int16.tobytes()

        # AudioSegment 생성
        audio_segment = AudioSegment(
            audio_bytes,
            frame_rate=self.sample_rate,
            sample_width=2,  # 16-bit = 2 bytes
            channels=self.channels,
        )

        return audio_segment

    def to_mono(self) -> "AudioFile":
        """
        오디오를 모노로 변환합니다.

        Returns:
            AudioFile: 모노 오디오 객체
        """
        if self.channels == 1:
            logger.debug("이미 모노 오디오입니다.")
            return self

        logger.info(f"오디오를 모노로 변환 중 ({self.channels}채널 -> 1채널)")

        if self.data.ndim == 2:
            # 다중 채널을 평균하여 모노로 변환
            mono_data = np.mean(self.data, axis=1)
        else:
            mono_data = self.data

        return AudioFile(mono_data, self.sample_rate, self.file_path)

    def resample(self, target_sr: int) -> "AudioFile":
        """
        오디오를 리샘플링합니다.

        Args:
            target_sr: 목표 샘플링 레이트

        Returns:
            AudioFile: 리샘플링된 오디오 객체
        """
        if self.sample_rate == target_sr:
            logger.debug(f"이미 목표 샘플링 레이트입니다: {target_sr}Hz")
            return self

        logger.info(f"오디오 리샘플링 중: {self.sample_rate}Hz -> {target_sr}Hz")

        resampled_data = librosa.resample(
            self.data,
            orig_sr=self.sample_rate,
            target_sr=target_sr,
        )

        return AudioFile(resampled_data, target_sr, self.file_path)

    def normalize(self, target_level: float = 1.0) -> "AudioFile":
        """
        오디오를 정규화합니다.

        Args:
            target_level: 목표 최대 진폭 (0.0 ~ 1.0)

        Returns:
            AudioFile: 정규화된 오디오 객체
        """
        logger.info(f"오디오 정규화 중 (목표 레벨: {target_level})")

        max_val = np.max(np.abs(self.data))
        if max_val == 0:
            logger.warning("오디오 데이터가 무음입니다. 정규화를 건너뜁니다.")
            return self

        normalized_data = self.data * (target_level / max_val)

        return AudioFile(normalized_data, self.sample_rate, self.file_path)

    def trim_silence(
        self,
        top_db: float = 30,
        frame_length: int = 2048,
        hop_length: int = 512,
    ) -> "AudioFile":
        """
        오디오의 앞뒤 무음 구간을 제거합니다.

        Args:
            top_db: 무음으로 간주할 dB 임계값
            frame_length: 프레임 길이
            hop_length: 홉 길이

        Returns:
            AudioFile: 무음이 제거된 오디오 객체
        """
        logger.info(f"무음 구간 제거 중 (임계값: {top_db}dB)")

        trimmed_data, _ = librosa.effects.trim(
            self.data,
            top_db=top_db,
            frame_length=frame_length,
            hop_length=hop_length,
        )

        logger.info(
            f"무음 제거 완료: {self.duration:.2f}초 -> {len(trimmed_data)/self.sample_rate:.2f}초"
        )

        return AudioFile(trimmed_data, self.sample_rate, self.file_path)

    def __repr__(self) -> str:
        """문자열 표현"""
        return (
            f"AudioFile(sample_rate={self.sample_rate}Hz, "
            f"channels={self.channels}, "
            f"duration={self.duration:.2f}s, "
            f"samples={self.num_samples})"
        )


__all__ = ["AudioFile"]
