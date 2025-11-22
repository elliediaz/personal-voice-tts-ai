"""
Batch TTS Processing

배치 TTS 처리 모듈
"""

import logging
from pathlib import Path
from typing import List, Optional
import time

from core.tts.pipeline import TTSPipeline

logger = logging.getLogger(__name__)


class BatchTTSProcessor:
    """배치 TTS 처리 클래스"""

    def __init__(self, pipeline: TTSPipeline):
        """
        Args:
            pipeline: TTS 파이프라인
        """
        self.pipeline = pipeline

        logger.info("BatchTTSProcessor 초기화")

    def process_texts(
        self,
        texts: List[str],
        source_files: List[Path],
        output_dir: Path,
        output_prefix: str = "output",
        show_progress: bool = True,
        **synthesis_kwargs,
    ) -> List[dict]:
        """
        여러 텍스트를 배치 처리

        Args:
            texts: 텍스트 리스트
            source_files: 소스 오디오 파일 리스트
            output_dir: 출력 디렉토리
            output_prefix: 출력 파일 접두사
            show_progress: 진행률 표시 여부
            **synthesis_kwargs: 합성 옵션

        Returns:
            메타데이터 리스트
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results = []
        start_time = time.time()

        logger.info(f"배치 처리 시작: {len(texts)}개 텍스트")

        for i, text in enumerate(texts, 1):
            logger.info(f"처리 중 ({i}/{len(texts)}): {text[:50]}...")

            # 출력 파일 경로
            output_path = output_dir / f"{output_prefix}_{i:03d}.wav"

            try:
                # TTS-to-Collage 실행
                metadata = self.pipeline.synthesize_collage(
                    text=text,
                    source_files=source_files,
                    output_path=output_path,
                    **synthesis_kwargs,
                )

                metadata["index"] = i
                metadata["success"] = True

                results.append(metadata)

                if show_progress:
                    progress = i / len(texts) * 100
                    print(f"[{progress:5.1f}%] 완료: {output_path}")

            except Exception as e:
                logger.error(f"처리 실패 ({i}/{len(texts)}): {str(e)}")

                results.append({
                    "index": i,
                    "text": text,
                    "success": False,
                    "error": str(e),
                })

        total_time = time.time() - start_time
        success_count = sum(1 for r in results if r.get("success", False))

        logger.info(
            f"배치 처리 완료: {success_count}/{len(texts)} 성공, "
            f"소요 시간: {total_time:.2f}초"
        )

        return results

    def process_from_file(
        self,
        input_file: Path,
        source_files: List[Path],
        output_dir: Path,
        **kwargs,
    ) -> List[dict]:
        """
        파일에서 텍스트를 읽어 배치 처리

        Args:
            input_file: 입력 텍스트 파일 (각 줄이 하나의 텍스트)
            source_files: 소스 오디오 파일 리스트
            output_dir: 출력 디렉토리
            **kwargs: 추가 옵션

        Returns:
            메타데이터 리스트
        """
        # 파일 읽기
        with open(input_file, 'r', encoding='utf-8') as f:
            texts = [line.strip() for line in f if line.strip()]

        logger.info(f"파일에서 {len(texts)}개 텍스트 로드: {input_file}")

        # 배치 처리
        return self.process_texts(
            texts=texts,
            source_files=source_files,
            output_dir=output_dir,
            **kwargs,
        )

    def __repr__(self) -> str:
        return f"BatchTTSProcessor(pipeline={self.pipeline})"
