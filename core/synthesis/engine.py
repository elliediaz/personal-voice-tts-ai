"""
Collage Engine

오디오 콜라주 및 합성 엔진
"""

import logging
from typing import List, Optional
from pathlib import Path
import time

import numpy as np

from core.audio.io import AudioFile
from algorithms.base import SimilarityMatch, BaseSimilarityAlgorithm
from core.synthesis.extractor import SegmentExtractor
from core.synthesis.blending import AudioBlender
from core.synthesis.pitch import PitchAdjuster
from core.synthesis.tempo import TempoAdjuster
from core.synthesis.prosody import ProsodyMatcher
from core.synthesis.enhancement import QualityEnhancer
from core.synthesis.cache import SegmentCache

logger = logging.getLogger(__name__)


class CollageEngine:
    """콜라주 엔진 클래스"""

    def __init__(
        self,
        similarity_algorithm: BaseSimilarityAlgorithm,
        extractor: Optional[SegmentExtractor] = None,
        blender: Optional[AudioBlender] = None,
        pitch_adjuster: Optional[PitchAdjuster] = None,
        tempo_adjuster: Optional[TempoAdjuster] = None,
        prosody_matcher: Optional[ProsodyMatcher] = None,
        enhancer: Optional[QualityEnhancer] = None,
        use_cache: bool = True,
    ):
        """
        Args:
            similarity_algorithm: 유사도 알고리즘
            extractor: 세그먼트 추출기
            blender: 오디오 블렌더
            pitch_adjuster: 피치 조정기
            tempo_adjuster: 템포 조정기
            prosody_matcher: 프로소디 매처
            enhancer: 품질 향상기
            use_cache: 캐시 사용 여부
        """
        self.similarity_algorithm = similarity_algorithm

        # 컴포넌트 초기화
        self.extractor = extractor or SegmentExtractor()
        self.blender = blender or AudioBlender()
        self.pitch_adjuster = pitch_adjuster or PitchAdjuster()
        self.tempo_adjuster = tempo_adjuster or TempoAdjuster()
        self.prosody_matcher = prosody_matcher or ProsodyMatcher()
        self.enhancer = enhancer or QualityEnhancer()

        # 캐시
        self.use_cache = use_cache
        if use_cache:
            self.cache = SegmentCache()
        else:
            self.cache = None

        logger.info(
            f"CollageEngine 초기화: algorithm={similarity_algorithm.__class__.__name__}"
        )

    def synthesize(
        self,
        target_audio: np.ndarray,
        target_sr: int,
        source_files: List[Path],
        top_k: int = 1,
        adjust_pitch: bool = True,
        adjust_tempo: bool = True,
        match_prosody: bool = True,
        enhance_quality: bool = True,
        progress_callback: Optional[callable] = None,
    ) -> tuple:
        """
        타겟 오디오를 소스 파일들로부터 합성

        Args:
            target_audio: 타겟 오디오
            target_sr: 타겟 샘플링 레이트
            source_files: 소스 파일 경로 리스트
            top_k: 각 소스에서 찾을 매치 수
            adjust_pitch: 피치 조정 여부
            adjust_tempo: 템포 조정 여부
            match_prosody: 프로소디 매칭 여부
            enhance_quality: 품질 향상 여부
            progress_callback: 진행률 콜백 함수

        Returns:
            (합성된 오디오, 샘플링 레이트, 메타데이터) 튜플
        """
        start_time = time.time()

        logger.info(
            f"합성 시작: {len(source_files)}개 소스 파일, "
            f"타겟 길이={len(target_audio) / target_sr:.2f}s"
        )

        # 1단계: 유사 세그먼트 찾기
        if progress_callback:
            progress_callback(0, "유사 세그먼트 검색 중...")

        all_matches = []
        for i, source_file in enumerate(source_files):
            logger.info(f"소스 파일 처리 중 ({i + 1}/{len(source_files)}): {source_file}")

            # 소스 오디오 로드
            source_audio_file = AudioFile.load(source_file)
            source_audio = source_audio_file.data
            source_sr = source_audio_file.sample_rate

            # 유사 세그먼트 찾기
            matches = self.similarity_algorithm.find_similar_segments(
                target_audio, source_audio, target_sr, source_sr, top_k=top_k
            )

            # 소스 파일 정보 추가
            for match in matches:
                if match.metadata is None:
                    match.metadata = {}
                match.metadata["source_file"] = str(source_file)

            all_matches.extend(matches)

            if progress_callback:
                progress = (i + 1) / len(source_files) * 0.3  # 30%까지
                progress_callback(progress, f"소스 {i + 1}/{len(source_files)} 처리 완료")

        if not all_matches:
            raise ValueError("유사한 세그먼트를 찾을 수 없습니다")

        # 최고의 매치만 선택 (top_k개)
        all_matches.sort(key=lambda m: m.similarity, reverse=True)
        best_match = all_matches[0]

        logger.info(f"{len(all_matches)}개 매치 발견, 최고 유사도: {best_match.similarity:.3f}")

        # 2단계: 세그먼트 추출
        if progress_callback:
            progress_callback(0.3, "세그먼트 추출 중...")

        # 최고 매치에서 세그먼트 추출
        source_file = Path(best_match.metadata["source_file"])
        source_audio_file = AudioFile.load(source_file)

        segment, segment_sr = self.extractor.extract_from_match(
            source_audio_file.data, source_audio_file.sample_rate, best_match
        )

        # 3단계: 피치 및 템포 조정
        if progress_callback:
            progress_callback(0.5, "피치/템포 조정 중...")

        adjusted = segment.copy()

        if adjust_tempo:
            logger.debug("템포 조정 적용")
            adjusted = self.tempo_adjuster.match_tempo(
                adjusted, target_audio, segment_sr
            )

        if adjust_pitch:
            logger.debug("피치 조정 적용")
            adjusted = self.pitch_adjuster.match_pitch_contour(
                adjusted, target_audio, segment_sr
            )

        # 4단계: 프로소디 매칭
        if match_prosody:
            if progress_callback:
                progress_callback(0.7, "프로소디 매칭 중...")

            logger.debug("프로소디 매칭 적용")
            adjusted = self.prosody_matcher.match_prosody(
                adjusted, target_audio, segment_sr
            )

        # 5단계: 품질 향상
        if enhance_quality:
            if progress_callback:
                progress_callback(0.9, "품질 향상 적용 중...")

            logger.debug("품질 향상 적용")
            adjusted = self.enhancer.enhance(adjusted, segment_sr)

        # 최종 정규화
        max_val = np.abs(adjusted).max()
        if max_val > 1.0:
            adjusted = adjusted / max_val * 0.99

        # 메타데이터 생성
        metadata = {
            "source_file": str(source_file),
            "similarity": float(best_match.similarity),
            "source_start": float(best_match.source_start),
            "source_end": float(best_match.source_end),
            "num_source_files": len(source_files),
            "num_matches": len(all_matches),
            "adjusted_pitch": adjust_pitch,
            "adjusted_tempo": adjust_tempo,
            "matched_prosody": match_prosody,
            "enhanced_quality": enhance_quality,
            "processing_time": time.time() - start_time,
        }

        if progress_callback:
            progress_callback(1.0, "합성 완료")

        logger.info(
            f"합성 완료: {metadata['processing_time']:.2f}초, "
            f"최고 유사도={metadata['similarity']:.3f}"
        )

        return adjusted, segment_sr, metadata

    def synthesize_from_file(
        self,
        target_file: Path,
        source_files: List[Path],
        output_file: Path,
        **kwargs,
    ) -> dict:
        """
        파일로부터 합성

        Args:
            target_file: 타겟 파일 경로
            source_files: 소스 파일 경로 리스트
            output_file: 출력 파일 경로
            **kwargs: synthesize()에 전달할 추가 인자

        Returns:
            메타데이터 딕셔너리
        """
        # 타겟 로드
        target = AudioFile.load(target_file)

        # 합성
        synthesized, sr, metadata = self.synthesize(
            target.data, target.sample_rate, source_files, **kwargs
        )

        # 저장
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        synthesized_file = AudioFile(synthesized, sr)
        synthesized_file.save(output_file)

        logger.info(f"합성 결과 저장: {output_file}")

        metadata["target_file"] = str(target_file)
        metadata["output_file"] = str(output_file)

        return metadata

    def __repr__(self) -> str:
        return f"CollageEngine(algorithm={self.similarity_algorithm.__class__.__name__})"
