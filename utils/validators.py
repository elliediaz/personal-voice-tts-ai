"""
Validation Utilities

입력 검증 및 유효성 검사 함수를 제공합니다.
"""

import os
from pathlib import Path
from typing import List, Optional, Union


def validate_audio_file(file_path: Union[str, Path], supported_formats: Optional[List[str]] = None) -> Path:
    """
    오디오 파일의 유효성을 검사합니다.

    Args:
        file_path: 검사할 파일 경로
        supported_formats: 지원하는 파일 포맷 리스트

    Returns:
        Path: 검증된 파일 경로

    Raises:
        FileNotFoundError: 파일이 존재하지 않을 때
        ValueError: 지원하지 않는 파일 포맷일 때
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

    if not file_path.is_file():
        raise ValueError(f"디렉토리가 아닌 파일이어야 합니다: {file_path}")

    if supported_formats:
        file_ext = file_path.suffix.lower().lstrip('.')
        if file_ext not in supported_formats:
            raise ValueError(
                f"지원하지 않는 파일 포맷입니다: {file_ext}. "
                f"지원 포맷: {', '.join(supported_formats)}"
            )

    return file_path


def validate_output_path(output_path: Union[str, Path], create_dir: bool = True) -> Path:
    """
    출력 경로의 유효성을 검사합니다.

    Args:
        output_path: 출력 파일 경로
        create_dir: 디렉토리 자동 생성 여부

    Returns:
        Path: 검증된 출력 경로

    Raises:
        ValueError: 잘못된 경로일 때
    """
    output_path = Path(output_path)

    if create_dir and not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)

    return output_path


def validate_sample_rate(sample_rate: int) -> int:
    """
    샘플링 레이트의 유효성을 검사합니다.

    Args:
        sample_rate: 샘플링 레이트 (Hz)

    Returns:
        int: 검증된 샘플링 레이트

    Raises:
        ValueError: 잘못된 샘플링 레이트일 때
    """
    if sample_rate <= 0:
        raise ValueError(f"샘플링 레이트는 양수여야 합니다: {sample_rate}")

    # 일반적인 샘플링 레이트 범위
    if not (8000 <= sample_rate <= 192000):
        raise ValueError(
            f"샘플링 레이트가 일반적인 범위를 벗어났습니다: {sample_rate}. "
            "일반적인 범위: 8000-192000 Hz"
        )

    return sample_rate


def validate_channels(channels: int) -> int:
    """
    채널 수의 유효성을 검사합니다.

    Args:
        channels: 채널 수

    Returns:
        int: 검증된 채널 수

    Raises:
        ValueError: 잘못된 채널 수일 때
    """
    if channels <= 0:
        raise ValueError(f"채널 수는 양수여야 합니다: {channels}")

    if channels > 8:
        raise ValueError(f"지원하지 않는 채널 수입니다: {channels}. 최대 8채널까지 지원합니다.")

    return channels


__all__ = [
    "validate_audio_file",
    "validate_output_path",
    "validate_sample_rate",
    "validate_channels",
]
