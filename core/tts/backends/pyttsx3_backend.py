"""
pyttsx3 Backend

오프라인 TTS 백엔드 (시스템 TTS 사용)
"""

import logging
from pathlib import Path
from typing import Optional
import tempfile

import numpy as np
import soundfile as sf

from core.tts.base import BaseTTSEngine

logger = logging.getLogger(__name__)


class Pyttsx3Backend(BaseTTSEngine):
    """pyttsx3 백엔드 (오프라인)"""

    def __init__(
        self,
        language: str = "ko",
        voice: Optional[str] = None,
        speech_rate: float = 150,
        volume: float = 1.0,
        **kwargs,
    ):
        """
        Args:
            language: 언어 코드
            voice: 음성 ID
            speech_rate: 말하기 속도 (단어/분)
            volume: 볼륨 (0.0~1.0)
        """
        super().__init__(language=language, voice=voice, volume=volume, **kwargs)
        self.speech_rate_wpm = speech_rate

        # pyttsx3 지연 로드
        try:
            import pyttsx3
            self.engine = pyttsx3.init()
            logger.info("pyttsx3 로드 성공")

            # 속도 및 볼륨 설정
            self.engine.setProperty('rate', speech_rate)
            self.engine.setProperty('volume', volume)

            # 음성 설정
            if voice:
                self.engine.setProperty('voice', voice)

        except ImportError:
            logger.error("pyttsx3를 설치해야 합니다: pip install pyttsx3")
            raise
        except Exception as e:
            logger.error(f"pyttsx3 초기화 실패: {str(e)}")
            raise

    def synthesize(
        self,
        text: str,
        output_path: Optional[Path] = None,
    ) -> tuple:
        """
        텍스트를 음성으로 합성

        Args:
            text: 합성할 텍스트
            output_path: 출력 파일 경로

        Returns:
            (audio_data, sample_rate) 튜플
        """
        if not self.validate_text(text):
            raise ValueError("유효하지 않은 텍스트입니다")

        logger.info(f"pyttsx3 합성 시작: {len(text)}자")

        # 임시 파일 또는 지정된 경로에 저장
        if output_path is None:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            output_path = Path(temp_file.name)
            temp_file.close()

        output_path = Path(output_path)

        # TTS 실행
        self.engine.save_to_file(text, str(output_path))
        self.engine.runAndWait()

        logger.info(f"pyttsx3 합성 완료: {output_path}")

        # 오디오 로드
        audio_data, sample_rate = sf.read(output_path)

        # 모노 변환
        if audio_data.ndim > 1:
            audio_data = np.mean(audio_data, axis=1)

        return audio_data, sample_rate

    def get_available_voices(self) -> list:
        """사용 가능한 음성 목록"""
        voices = self.engine.getProperty('voices')
        return [v.id for v in voices]

    def __repr__(self) -> str:
        return f"Pyttsx3Backend(language={self.language}, rate={self.speech_rate_wpm})"
