"""
TTS-to-Collage Pipeline

텍스트에서 콜라주 음성까지의 전체 파이프라인
"""

import logging
from pathlib import Path
from typing import Optional, List
import tempfile

import numpy as np

from core.tts.base import BaseTTSEngine
from core.tts.preprocessing import TextPreprocessor
from core.synthesis.engine import CollageEngine
from core.audio.io import AudioFile
from algorithms.base import BaseSimilarityAlgorithm

logger = logging.getLogger(__name__)


class TTSPipeline:
    """TTS-to-Collage 파이프라인"""

    def __init__(
        self,
        tts_engine: BaseTTSEngine,
        similarity_algorithm: BaseSimilarityAlgorithm,
        preprocessor: Optional[TextPreprocessor] = None,
    ):
        """
        Args:
            tts_engine: TTS 엔진
            similarity_algorithm: 유사도 알고리즘
            preprocessor: 텍스트 전처리기 (옵션)
        """
        self.tts_engine = tts_engine
        self.similarity_algorithm = similarity_algorithm
        self.preprocessor = preprocessor or TextPreprocessor()

        # 콜라주 엔진 초기화
        self.collage_engine = CollageEngine(similarity_algorithm=similarity_algorithm)

        logger.info(
            f"TTSPipeline 초기화: "
            f"tts={tts_engine.__class__.__name__}, "
            f"algorithm={similarity_algorithm.__class__.__name__}"
        )

    def synthesize_collage(
        self,
        text: str,
        source_files: List[Path],
        output_path: Path,
        preprocess_text: bool = True,
        **synthesis_kwargs,
    ) -> dict:
        """
        텍스트에서 콜라주 음성까지 생성

        Args:
            text: 입력 텍스트
            source_files: 소스 오디오 파일 리스트
            output_path: 출력 파일 경로
            preprocess_text: 텍스트 전처리 여부
            **synthesis_kwargs: 합성 옵션

        Returns:
            메타데이터 딕셔너리
        """
        logger.info(f"TTS-to-Collage 파이프라인 시작: {len(text)}자")

        # 1단계: 텍스트 전처리
        if preprocess_text:
            logger.info("텍스트 전처리 중...")
            processed_text = self.preprocessor.preprocess(text)
        else:
            processed_text = text

        # 2단계: TTS로 타겟 오디오 생성
        logger.info("TTS 합성 중...")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            temp_tts_path = Path(temp_file.name)

        target_audio, target_sr = self.tts_engine.synthesize(
            processed_text, output_path=temp_tts_path
        )

        logger.info(f"TTS 완료: {len(target_audio) / target_sr:.2f}초")

        # 3단계: 콜라주 합성
        logger.info("콜라주 합성 중...")
        metadata = self.collage_engine.synthesize_from_file(
            target_file=temp_tts_path,
            source_files=source_files,
            output_file=output_path,
            **synthesis_kwargs,
        )

        # 임시 파일 삭제
        temp_tts_path.unlink()

        # 메타데이터에 TTS 정보 추가
        metadata["tts_engine"] = self.tts_engine.__class__.__name__
        metadata["original_text"] = text
        metadata["processed_text"] = processed_text

        logger.info(f"TTS-to-Collage 완료: {output_path}")

        return metadata

    def synthesize_tts_only(
        self,
        text: str,
        output_path: Path,
        preprocess_text: bool = True,
    ) -> tuple:
        """
        TTS만 실행 (콜라주 없이)

        Args:
            text: 입력 텍스트
            output_path: 출력 파일 경로
            preprocess_text: 텍스트 전처리 여부

        Returns:
            (audio_data, sample_rate) 튜플
        """
        # 텍스트 전처리
        if preprocess_text:
            processed_text = self.preprocessor.preprocess(text)
        else:
            processed_text = text

        # TTS 실행
        audio_data, sample_rate = self.tts_engine.synthesize(
            processed_text, output_path=output_path
        )

        return audio_data, sample_rate

    def __repr__(self) -> str:
        return (
            f"TTSPipeline("
            f"tts={self.tts_engine.__class__.__name__}, "
            f"algorithm={self.similarity_algorithm.__class__.__name__})"
        )
