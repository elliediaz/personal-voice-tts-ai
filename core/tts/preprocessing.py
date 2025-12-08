"""
Text Preprocessing

텍스트 전처리 모듈
"""

import logging
import re

logger = logging.getLogger(__name__)


class TextPreprocessor:
    """텍스트 전처리 클래스"""

    def __init__(self, language: str = "ko"):
        """
        Args:
            language: 언어 코드
        """
        self.language = language

        logger.info(f"TextPreprocessor 초기화: language={language}")

    def preprocess(self, text: str) -> str:
        """
        텍스트 전처리

        Args:
            text: 원본 텍스트

        Returns:
            전처리된 텍스트
        """
        # 1. 공백 정규화
        text = self.normalize_whitespace(text)

        # 2. 숫자를 단어로 변환
        text = self.numbers_to_words(text)

        # 3. 약어 확장
        text = self.expand_abbreviations(text)

        # 4. 특수 문자 처리
        text = self.handle_special_characters(text)

        return text

    def normalize_whitespace(self, text: str) -> str:
        """공백 정규화"""
        # 연속된 공백을 하나로
        text = re.sub(r'\s+', ' ', text)

        # 앞뒤 공백 제거
        text = text.strip()

        return text

    def numbers_to_words(self, text: str) -> str:
        """숫자를 단어로 변환"""
        if self.language == "ko":
            # 한국어 숫자 변환 (간단한 구현)
            def korean_number(match):
                num = int(match.group())
                if num == 0:
                    return "영"

                units = ["", "일", "이", "삼", "사", "오", "육", "칠", "팔", "구"]
                tens = ["", "십", "이십", "삼십", "사십", "오십", "육십", "칠십", "팔십", "구십"]

                if num < 10:
                    return units[num]
                elif num < 100:
                    return tens[num // 10] + (units[num % 10] if num % 10 != 0 else "")
                else:
                    # 100 이상은 그대로 (간단한 구현)
                    return str(num)

            # 한국어에서는 \b가 제대로 작동하지 않으므로 숫자 패턴만 사용
            text = re.sub(r'\d+', korean_number, text)

        return text

    def expand_abbreviations(self, text: str) -> str:
        """약어 확장"""
        if self.language == "ko":
            abbreviations = {
                "TTS": "티티에스",
                "AI": "에이아이",
                "API": "에이피아이",
                "URL": "유알엘",
                "etc": "기타",
            }

            for abbr, expanded in abbreviations.items():
                text = re.sub(r'\b' + abbr + r'\b', expanded, text, flags=re.IGNORECASE)

        return text

    def handle_special_characters(self, text: str) -> str:
        """특수 문자 처리"""
        # 이메일, URL 등은 제거하거나 읽기 쉽게 변환
        text = re.sub(r'http[s]?://\S+', ' 링크 ', text)
        text = re.sub(r'\S+@\S+', ' 이메일 ', text)

        # 불필요한 특수 문자 제거 (문장 부호는 유지)
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\'\"]', '', text)

        return text

    def split_sentences(self, text: str) -> list:
        """문장 분리"""
        # 간단한 문장 분리 (마침표, 느낌표, 물음표 기준)
        sentences = re.split(r'[\.!?]+', text)

        # 빈 문장 제거 및 공백 정리
        sentences = [s.strip() for s in sentences if s.strip()]

        return sentences

    def __repr__(self) -> str:
        return f"TextPreprocessor(language={self.language})"
