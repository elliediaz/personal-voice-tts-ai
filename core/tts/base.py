"""
Base TTS Engine

TTS 엔진의 추상 베이스 클래스
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any

import numpy as np

logger = logging.getLogger(__name__)


class BaseTTSEngine(ABC):
    """TTS 엔진 베이스 클래스"""

    def __init__(
        self,
        language: str = "ko",
        voice: Optional[str] = None,
        speech_rate: float = 1.0,
        pitch: float = 1.0,
        volume: float = 1.0,
    ):
        """
        Args:
            language: 언어 코드 (예: 'ko', 'en', 'ja')
            voice: 음성 이름 (백엔드마다 다름)
            speech_rate: 말하기 속도 (1.0=보통)
            pitch: 피치 (1.0=보통)
            volume: 볼륨 (1.0=보통)
        """
        self.language = language
        self.voice = voice
        self.speech_rate = speech_rate
        self.pitch = pitch
        self.volume = volume

        logger.info(
            f"{self.__class__.__name__} 초기화: "
            f"language={language}, voice={voice}"
        )

    @abstractmethod
    def synthesize(
        self,
        text: str,
        output_path: Optional[Path] = None,
    ) -> tuple:
        """
        텍스트를 음성으로 합성

        Args:
            text: 합성할 텍스트
            output_path: 출력 파일 경로 (옵션)

        Returns:
            (audio_data, sample_rate) 튜플
        """
        pass

    @abstractmethod
    def get_available_voices(self) -> list:
        """
        사용 가능한 음성 목록 반환

        Returns:
            음성 이름 리스트
        """
        pass

    def validate_text(self, text: str) -> bool:
        """
        텍스트 유효성 검증

        Args:
            text: 검증할 텍스트

        Returns:
            유효하면 True
        """
        if not text or not text.strip():
            logger.warning("빈 텍스트입니다")
            return False

        if len(text) > 5000:
            logger.warning("텍스트가 너무 깁니다 (5000자 초과)")
            return False

        return True

    def get_info(self) -> Dict[str, Any]:
        """
        TTS 엔진 정보 반환

        Returns:
            정보 딕셔너리
        """
        return {
            "engine": self.__class__.__name__,
            "language": self.language,
            "voice": self.voice,
            "speech_rate": self.speech_rate,
            "pitch": self.pitch,
            "volume": self.volume,
        }

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"language={self.language}, "
            f"voice={self.voice})"
        )
