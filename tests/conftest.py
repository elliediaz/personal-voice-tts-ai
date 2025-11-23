"""
Pytest Configuration and Fixtures

테스트에 사용되는 공통 픽스처와 설정을 정의합니다.
"""

import numpy as np
import pytest
from pathlib import Path


@pytest.fixture
def sample_audio_mono():
    """
    모노 오디오 샘플을 생성합니다.

    Returns:
        tuple: (audio_data, sample_rate)
    """
    sample_rate = 22050
    duration = 1.0  # 1초
    frequency = 440.0  # A4 note

    # 사인파 생성
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = np.sin(2 * np.pi * frequency * t).astype(np.float32)

    return audio_data, sample_rate


@pytest.fixture
def sample_audio_stereo():
    """
    스테레오 오디오 샘플을 생성합니다.

    Returns:
        tuple: (audio_data, sample_rate)
    """
    sample_rate = 22050
    duration = 1.0  # 1초
    frequency_left = 440.0  # A4 note
    frequency_right = 554.37  # C#5 note

    # 각 채널에 다른 주파수의 사인파 생성
    t = np.linspace(0, duration, int(sample_rate * duration))
    left_channel = np.sin(2 * np.pi * frequency_left * t).astype(np.float32)
    right_channel = np.sin(2 * np.pi * frequency_right * t).astype(np.float32)

    # 스테레오로 결합
    audio_data = np.column_stack((left_channel, right_channel))

    return audio_data, sample_rate


@pytest.fixture
def temp_audio_file(tmp_path, sample_audio_mono):
    """
    임시 오디오 파일을 생성합니다.

    Args:
        tmp_path: pytest의 임시 디렉토리
        sample_audio_mono: 모노 오디오 샘플

    Returns:
        Path: 생성된 임시 파일 경로
    """
    import soundfile as sf

    audio_data, sample_rate = sample_audio_mono
    file_path = tmp_path / "test_audio.wav"

    sf.write(str(file_path), audio_data, sample_rate)

    return file_path


@pytest.fixture
def analyzer():
    """
    AudioAnalyzer 인스턴스를 생성합니다.

    Returns:
        AudioAnalyzer: 분석기 객체
    """
    from core.audio.analysis import AudioAnalyzer

    return AudioAnalyzer()


@pytest.fixture
def config():
    """
    테스트용 설정을 로드합니다.

    Returns:
        Config: 설정 객체
    """
    from config import get_config

    return get_config()
