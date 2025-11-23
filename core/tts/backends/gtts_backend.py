"""
gTTS Backend

Google Text-to-Speech 백엔드
"""

import logging
from pathlib import Path
from typing import Optional
import tempfile

import numpy as np
import soundfile as sf

from core.tts.base import BaseTTSEngine

logger = logging.getLogger(__name__)


class GTTSBackend(BaseTTSEngine):
    """gTTS 백엔드"""

    def __init__(
        self,
        language: str = "ko",
        tld: str = "com",
        slow: bool = False,
        **kwargs,
    ):
        """
        Args:
            language: 언어 코드
            tld: 도메인 (com, co.kr, co.uk 등)
            slow: 느린 음성 여부
        """
        super().__init__(language=language, **kwargs)
        self.tld = tld
        self.slow = slow

        # gTTS 지연 로드
        try:
            from gtts import gTTS
            self.gTTS = gTTS
            logger.info("gTTS 로드 성공")
        except ImportError:
            logger.error("gTTS를 설치해야 합니다: pip install gtts")
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

        logger.info(f"gTTS 합성 시작: {len(text)}자")

        # gTTS 객체 생성
        tts = self.gTTS(
            text=text,
            lang=self.language,
            tld=self.tld,
            slow=self.slow,
        )

        # 임시 파일 또는 지정된 경로에 저장
        if output_path is None:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            output_path = Path(temp_file.name)
            temp_file.close()

        output_path = Path(output_path)
        tts.save(str(output_path))

        logger.info(f"gTTS 합성 완료: {output_path}")

        # 오디오 로드
        audio_data, sample_rate = sf.read(output_path)

        # 모노 변환
        if audio_data.ndim > 1:
            audio_data = np.mean(audio_data, axis=1)

        return audio_data, sample_rate

    def get_available_voices(self) -> list:
        """사용 가능한 음성 목록 (gTTS는 언어만 지원)"""
        # gTTS는 다양한 언어를 지원하지만 음성 선택은 불가
        return [self.language]

    def __repr__(self) -> str:
        return f"GTTSBackend(language={self.language}, tld={self.tld})"
