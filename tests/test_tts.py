"""
Tests for TTS Modules
"""

import pytest
from pathlib import Path

from core.tts.base import BaseTTSEngine
from core.tts.preprocessing import TextPreprocessor


class MockTTSEngine(BaseTTSEngine):
    """테스트용 Mock TTS 엔진"""

    def synthesize(self, text, output_path=None):
        import numpy as np
        # 더미 오디오 데이터 반환
        audio = np.random.randn(16000).astype(np.float32)
        return audio, 16000

    def get_available_voices(self):
        return ["mock_voice_1", "mock_voice_2"]


class TestBaseTTSEngine:
    """BaseTTSEngine 테스트"""

    def test_init(self):
        """초기화 테스트"""
        engine = MockTTSEngine(language="ko", speech_rate=1.0)

        assert engine.language == "ko"
        assert engine.speech_rate == 1.0

    def test_validate_text(self):
        """텍스트 검증 테스트"""
        engine = MockTTSEngine()

        assert engine.validate_text("안녕하세요") == True
        assert engine.validate_text("") == False
        assert engine.validate_text("   ") == False

    def test_get_info(self):
        """정보 반환 테스트"""
        engine = MockTTSEngine(language="ko", voice="test_voice")

        info = engine.get_info()

        assert isinstance(info, dict)
        assert info["language"] == "ko"
        assert info["voice"] == "test_voice"


class TestTextPreprocessor:
    """TextPreprocessor 테스트"""

    def test_init(self):
        """초기화 테스트"""
        preprocessor = TextPreprocessor(language="ko")

        assert preprocessor.language == "ko"

    def test_normalize_whitespace(self):
        """공백 정규화 테스트"""
        preprocessor = TextPreprocessor()

        text = "안녕하세요    반갑습니다"
        normalized = preprocessor.normalize_whitespace(text)

        assert "    " not in normalized
        assert normalized == "안녕하세요 반갑습니다"

    def test_numbers_to_words_korean(self):
        """한국어 숫자 변환 테스트"""
        preprocessor = TextPreprocessor(language="ko")

        text = "나는 1살입니다"
        converted = preprocessor.numbers_to_words(text)

        assert "1" not in converted
        assert "일" in converted

    def test_split_sentences(self):
        """문장 분리 테스트"""
        preprocessor = TextPreprocessor()

        text = "안녕하세요. 반갑습니다! 어떻게 지내세요?"
        sentences = preprocessor.split_sentences(text)

        assert len(sentences) == 3
        assert "안녕하세요" in sentences[0]
        assert "반갑습니다" in sentences[1]

    def test_preprocess(self):
        """전체 전처리 테스트"""
        preprocessor = TextPreprocessor(language="ko")

        text = "안녕하세요   반갑습니다"
        processed = preprocessor.preprocess(text)

        assert isinstance(processed, str)
        assert "   " not in processed


class TestTTSBackends:
    """TTS 백엔드 테스트 (선택적)"""

    @pytest.mark.skipif(True, reason="실제 TTS 백엔드 테스트는 선택적")
    def test_gtts_backend(self):
        """gTTS 백엔드 테스트"""
        from core.tts.backends import GTTSBackend

        backend = GTTSBackend(language="ko")
        assert backend.language == "ko"

    @pytest.mark.skipif(True, reason="실제 TTS 백엔드 테스트는 선택적")
    def test_pyttsx3_backend(self):
        """pyttsx3 백엔드 테스트"""
        from core.tts.backends import Pyttsx3Backend

        backend = Pyttsx3Backend(language="ko")
        assert backend.language == "ko"
