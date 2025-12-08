"""
Configuration Module

프로젝트 설정을 로드하고 관리하는 모듈입니다.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml
from pydantic import BaseModel


class AudioConfig(BaseModel):
    """오디오 처리 설정"""
    default_sample_rate: int = 22050
    default_channels: int = 1
    normalize: bool = True
    supported_formats: list = ["wav", "mp3", "flac", "ogg", "m4a"]
    analysis: Dict[str, Any] = {}


class OutputConfig(BaseModel):
    """출력 설정"""
    default_dir: str = "./output"
    default_format: str = "wav"
    quality: int = 8
    include_metadata: bool = True


class LoggingConfig(BaseModel):
    """로깅 설정"""
    level: str = "INFO"
    file: str = "./logs/app.log"
    console: bool = True
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"


class PerformanceConfig(BaseModel):
    """성능 설정"""
    num_workers: int = 0
    use_cache: bool = True
    cache_dir: str = "./cache"
    max_memory_mb: int = 0


class VisualizationConfig(BaseModel):
    """시각화 설정"""
    dpi: int = 100
    figure_size: list = [12, 6]
    colormap: str = "viridis"
    font_size: int = 10


class Config(BaseModel):
    """전체 설정"""
    audio: AudioConfig = AudioConfig()
    output: OutputConfig = OutputConfig()
    logging: LoggingConfig = LoggingConfig()
    performance: PerformanceConfig = PerformanceConfig()
    visualization: VisualizationConfig = VisualizationConfig()


def load_config(config_path: Optional[str] = None) -> Config:
    """
    설정 파일을 로드합니다.

    우선순위:
    1. config_path로 지정된 파일
    2. config.local.yml
    3. config.yml
    4. config.default.yml

    Args:
        config_path: 설정 파일 경로 (선택사항)

    Returns:
        Config: 로드된 설정 객체
    """
    # 프로젝트 루트 디렉토리
    project_root = Path(__file__).parent.parent
    config_dir = project_root / "config"

    # 기본 설정 로드
    default_config_path = config_dir / "config.default.yml"
    with open(default_config_path, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    # 사용자 설정 파일 우선순위
    user_config_paths = [
        config_path,
        config_dir / "config.local.yml",
        config_dir / "config.yml",
    ]

    # 존재하는 사용자 설정 파일 로드 및 병합
    for user_config_path in user_config_paths:
        if user_config_path and Path(user_config_path).exists():
            with open(user_config_path, "r", encoding="utf-8") as f:
                user_config = yaml.safe_load(f)
                if user_config:
                    _merge_config(config_data, user_config)
            break

    return Config(**config_data)


def _merge_config(base: Dict, override: Dict) -> None:
    """
    설정을 재귀적으로 병합합니다.

    Args:
        base: 기본 설정 딕셔너리
        override: 오버라이드할 설정 딕셔너리
    """
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _merge_config(base[key], value)
        else:
            base[key] = value


# 전역 설정 인스턴스
_config: Optional[Config] = None


def get_config() -> Config:
    """
    전역 설정 인스턴스를 반환합니다.

    Returns:
        Config: 설정 객체
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reload_config(config_path: Optional[str] = None) -> Config:
    """
    설정을 다시 로드합니다.

    Args:
        config_path: 설정 파일 경로 (선택사항)

    Returns:
        Config: 재로드된 설정 객체
    """
    global _config
    _config = load_config(config_path)
    return _config


__all__ = [
    "Config",
    "AudioConfig",
    "OutputConfig",
    "LoggingConfig",
    "PerformanceConfig",
    "VisualizationConfig",
    "load_config",
    "get_config",
    "reload_config",
]
