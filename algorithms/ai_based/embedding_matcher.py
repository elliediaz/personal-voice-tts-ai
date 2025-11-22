"""
Embedding-based Similarity Matcher

임베딩 기반 오디오 유사도 검출 알고리즘
"""

import logging
from typing import Optional, List
import time

import numpy as np
import librosa

from algorithms.base import BaseSimilarityAlgorithm, SimilarityMatch
from algorithms.ai_based.embeddings import EmbeddingExtractor
from core.ai.metadata import AIMetadata

logger = logging.getLogger(__name__)


class EmbeddingSimilarity(BaseSimilarityAlgorithm):
    """임베딩 기반 유사도 알고리즘"""

    def __init__(
        self,
        model_name: str = "wav2vec2-base",
        pooling: str = "mean",
        normalize: bool = True,
        distance_metric: str = "cosine",
        window_size: float = 1.0,
        hop_size: float = 0.5,
        use_faiss: bool = False,
        device: Optional[str] = None,
        **kwargs,
    ):
        """
        Args:
            model_name: 사용할 모델 이름
            pooling: 풀링 방법 ('mean', 'max', 'attention')
            normalize: 임베딩 정규화 여부
            distance_metric: 거리 메트릭 ('cosine', 'euclidean')
            window_size: 슬라이딩 윈도우 크기 (초)
            hop_size: 슬라이딩 윈도우 이동 크기 (초)
            use_faiss: FAISS 사용 여부 (빠른 검색)
            device: 디바이스 ('cuda', 'cpu')
        """
        super().__init__(**kwargs)

        self.model_name = model_name
        self.pooling = pooling
        self.normalize = normalize
        self.distance_metric = distance_metric
        self.window_size = window_size
        self.hop_size = hop_size
        self.use_faiss = use_faiss

        # 임베딩 추출기 초기화
        self.extractor = EmbeddingExtractor(
            model_name=model_name,
            pooling=pooling,
            normalize=normalize,
            device=device,
        )

        # FAISS 인덱스 (옵션)
        self.faiss_index = None
        if use_faiss:
            try:
                import faiss

                self.faiss = faiss
                logger.info("FAISS 사용 가능")
            except ImportError:
                logger.warning("FAISS를 사용할 수 없습니다. pip install faiss-cpu")
                self.use_faiss = False

        logger.info(
            f"EmbeddingSimilarity 초기화: {model_name} "
            f"(metric={distance_metric}, window={window_size}s)"
        )

    def compute_similarity(
        self,
        target_audio: np.ndarray,
        source_audio: np.ndarray,
        target_sr: int,
        source_sr: int,
    ) -> float:
        """
        두 오디오 간의 유사도 계산

        Args:
            target_audio: 타겟 오디오
            source_audio: 소스 오디오
            target_sr: 타겟 샘플링 레이트
            source_sr: 소스 샘플링 레이트

        Returns:
            유사도 (0~1, 높을수록 유사)
        """
        self._validate_audio(target_audio, target_sr, "target_audio")
        self._validate_audio(source_audio, source_sr, "source_audio")

        # 임베딩 추출
        target_emb = self.extractor.extract(target_audio, target_sr)
        source_emb = self.extractor.extract(source_audio, source_sr)

        # 유사도 계산
        similarity = self._compute_embedding_similarity(target_emb, source_emb)

        return float(similarity)

    def find_similar_segments(
        self,
        target_audio: np.ndarray,
        source_audio: np.ndarray,
        target_sr: int,
        source_sr: int,
        top_k: int = 10,
    ) -> List[SimilarityMatch]:
        """
        유사한 세그먼트 찾기

        Args:
            target_audio: 타겟 오디오
            source_audio: 소스 오디오
            target_sr: 타겟 샘플링 레이트
            source_sr: 소스 샘플링 레이트
            top_k: 반환할 최대 매치 수

        Returns:
            유사도 매치 리스트
        """
        self._validate_audio(target_audio, target_sr, "target_audio")
        self._validate_audio(source_audio, source_sr, "source_audio")

        start_time = time.time()

        # 타겟 임베딩 추출
        target_emb, target_inf_time = self.extractor.extract(
            target_audio, target_sr, return_time=True
        )

        target_duration = len(target_audio) / target_sr

        # 소스 오디오를 슬라이딩 윈도우로 분할
        window_samples = int(self.window_size * source_sr)
        hop_samples = int(self.hop_size * source_sr)

        source_segments = []
        source_times = []

        for start in range(0, len(source_audio) - window_samples + 1, hop_samples):
            end = start + window_samples
            segment = source_audio[start:end]

            start_time_sec = start / source_sr
            end_time_sec = end / source_sr

            source_segments.append(segment)
            source_times.append((start_time_sec, end_time_sec))

        if not source_segments:
            logger.warning("소스 오디오가 너무 짧습니다")
            return []

        # 소스 임베딩 추출 (배치)
        logger.info(f"{len(source_segments)}개의 소스 세그먼트에서 임베딩 추출 중...")
        source_embs = self.extractor.extract_batch(
            source_segments,
            [source_sr] * len(source_segments),
            show_progress=True,
        )

        # 유사도 계산
        similarities = []
        for source_emb in source_embs:
            sim = self._compute_embedding_similarity(target_emb, source_emb)
            similarities.append(sim)

        # SimilarityMatch 생성
        matches = []
        for i, (sim, (src_start, src_end)) in enumerate(
            zip(similarities, source_times)
        ):
            match = SimilarityMatch(
                target_start=0.0,
                target_end=target_duration,
                source_start=src_start,
                source_end=src_end,
                similarity=float(sim),
                confidence=float(sim),  # 임베딩 유사도를 신뢰도로 사용
                metadata={
                    "algorithm": "embedding",
                    "model": self.model_name,
                    "pooling": self.pooling,
                    "segment_index": i,
                },
            )
            matches.append(match)

        # 필터링 및 정렬
        matches = self._filter_matches(matches, top_k=top_k)

        total_time = time.time() - start_time
        logger.info(
            f"{len(matches)}개의 유사 세그먼트 발견 (소요 시간: {total_time:.2f}초)"
        )

        return matches

    def _compute_embedding_similarity(
        self, emb1: np.ndarray, emb2: np.ndarray
    ) -> float:
        """
        두 임베딩 간의 유사도 계산

        Args:
            emb1: 첫 번째 임베딩
            emb2: 두 번째 임베딩

        Returns:
            유사도 (0~1)
        """
        if self.distance_metric == "cosine":
            # 코사인 유사도
            similarity = np.dot(emb1, emb2) / (
                np.linalg.norm(emb1) * np.linalg.norm(emb2) + 1e-8
            )
            # [-1, 1] -> [0, 1]
            similarity = (similarity + 1) / 2
        elif self.distance_metric == "euclidean":
            # 유클리드 거리를 유사도로 변환
            distance = np.linalg.norm(emb1 - emb2)
            # 거리를 유사도로 변환 (작을수록 높음)
            similarity = 1 / (1 + distance)
        else:
            raise ValueError(f"지원하지 않는 거리 메트릭: {self.distance_metric}")

        return float(np.clip(similarity, 0, 1))

    def create_metadata(
        self,
        inference_time: float,
        num_matches: int,
        similarities: List[float],
        frequency_analysis: Optional[dict] = None,
    ) -> AIMetadata:
        """
        AI 메타데이터 생성

        Args:
            inference_time: 추론 시간
            num_matches: 매치 개수
            similarities: 유사도 리스트
            frequency_analysis: 주파수 분석 결과

        Returns:
            AIMetadata
        """
        avg_confidence = sum(similarities) / len(similarities) if similarities else 0.0

        metadata = AIMetadata(
            model_name=self.model_name,
            model_type="wav2vec2" if "wav2vec2" in self.model_name else "hubert",
            inference_time=inference_time,
            device=self.extractor.device,
            embedding_dim=self.extractor.get_embedding_dim(),
            confidence_score=avg_confidence,
            similarity_scores=similarities,
            frequency_analysis=frequency_analysis,
            metadata={
                "pooling": self.pooling,
                "distance_metric": self.distance_metric,
                "num_matches": num_matches,
                "window_size": self.window_size,
                "hop_size": self.hop_size,
            },
        )

        return metadata

    def __repr__(self) -> str:
        return (
            f"EmbeddingSimilarity(model={self.model_name}, "
            f"metric={self.distance_metric})"
        )
