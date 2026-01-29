"""
Edge-TTS Backend

Microsoft Edge TTS 백엔드
"""

import logging
from pathlib import Path
from typing import Optional
import tempfile
import asyncio

import numpy as np
import soundfile as sf

from core.tts.base import BaseTTSEngine

logger = logging.getLogger(__name__)


class EdgeTTSBackend(BaseTTSEngine):
    """Edge-TTS 백엔드"""

    def __init__(
        self,
        language: str = "ko-KR",
        voice: Optional[str] = None,
        speech_rate: float = 1.0,
        pitch: float = 1.0,
        volume: float = 1.0,
        **kwargs,
    ):
        """
        Args:
            language: 언어 코드
            voice: 음성 이름 (예: ko-KR-SunHiNeural)
            speech_rate: 말하기 속도 (0.5~2.0, 기본 1.0)
            pitch: 음높이 (0.5~2.0, 기본 1.0)
            volume: 볼륨 (0.0~1.0, 기본 1.0)
        """
        super().__init__(language=language, voice=voice, volume=volume, **kwargs)
        self.speech_rate = speech_rate
        self.pitch = pitch

        # edge-tts 지연 로드
        try:
            import edge_tts
            self.edge_tts = edge_tts
            logger.info("edge-tts 로드 성공")

            # 기본 음성 설정
            if voice is None:
                if language.startswith("ko"):
                    self.voice = "ko-KR-SunHiNeural"
                elif language.startswith("en"):
                    self.voice = "en-US-AriaNeural"
                elif language.startswith("ja"):
                    self.voice = "ja-JP-NanamiNeural"
                else:
                    self.voice = "en-US-AriaNeural"

        except ImportError:
            logger.error("edge-tts를 설치해야 합니다: pip install edge-tts")
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

        logger.info(f"Edge-TTS 합성 시작: {len(text)}자")

        # 임시 파일 또는 지정된 경로에 저장
        if output_path is None:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            output_path = Path(temp_file.name)
            temp_file.close()

        output_path = Path(output_path)

        # 비동기 TTS 실행
        asyncio.run(self._async_synthesize(text, output_path))

        logger.info(f"Edge-TTS 합성 완료: {output_path}")

        # 오디오 로드
        audio_data, sample_rate = sf.read(output_path)

        # 모노 변환
        if audio_data.ndim > 1:
            audio_data = np.mean(audio_data, axis=1)

        return audio_data, sample_rate

    async def _async_synthesize(self, text: str, output_path: Path):
        """비동기 TTS 합성"""
        # 속도 및 피치를 SSML 형식 문자열로 변환
        # rate: +50%, -25% 형식 (100% = 1.0x)
        rate_percent = int((self.speech_rate - 1.0) * 100)
        rate_str = f"+{rate_percent}%" if rate_percent >= 0 else f"{rate_percent}%"

        # pitch: +50Hz, -25Hz 형식 (1.0x = 0Hz 기준으로 50Hz 스케일)
        pitch_hz = int((self.pitch - 1.0) * 50)
        pitch_str = f"+{pitch_hz}Hz" if pitch_hz >= 0 else f"{pitch_hz}Hz"

        # 볼륨: +0% ~ -100% 형식
        volume_percent = int((self.volume - 1.0) * 100)
        volume_str = f"+{volume_percent}%" if volume_percent >= 0 else f"{volume_percent}%"

        communicate = self.edge_tts.Communicate(
            text, self.voice, rate=rate_str, pitch=pitch_str, volume=volume_str
        )
        await communicate.save(str(output_path))

    def get_available_voices(self) -> list:
        """사용 가능한 음성 목록"""
        # Edge-TTS는 많은 음성을 지원하지만 여기서는 간단히 처리
        return [self.voice]

    @staticmethod
    async def list_voices():
        """모든 사용 가능한 음성 목록 (비동기)"""
        import edge_tts
        voices = await edge_tts.list_voices()
        return voices

    def __repr__(self) -> str:
        return f"EdgeTTSBackend(language={self.language}, voice={self.voice}, rate={self.speech_rate}, pitch={self.pitch})"
