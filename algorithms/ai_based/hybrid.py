"""
Hybrid Similarity Algorithm

전통적 알고리즘과 AI 기반 알고리즘을 결합한 하이브리드 유사도 검출
"""

import logging
from typing import List, Optional, Dict, Any

import numpy as np

from algorithms.base import BaseSimilarityAlgorithm, SimilarityMatch
from algorithms.ai_based.embedding_matcher import EmbeddingSimilarity
from algorithms.traditional.mfcc import MFCCSimilarity

logger = logging.getLogger(__name__)


class HybridSimilarity(BaseSimilarityAlgorithm):
    """하이브리드 유사도 알고리즘 (전통적 + AI)"""

    def __init__(
        self,
        traditional_algorithm: Optional[BaseSimilarityAlgorithm] = None,
        ai_algorithm: Optional[EmbeddingSimilarity] = None,
        traditional_weight: float = 0.4,
        ai_weight: float = 0.6,
        fusion_method: str = "weighted_average",
        **kwargs,
    ):
        """
        Args:
            traditional_algorithm: 전통적 알고리즘 (None이면 MFCC 사용)
            ai_algorithm: AI 알고리즘 (None이면 기본 임베딩 사용)
            traditional_weight: 전통적 알고리즘 가중치
            ai_weight: AI 알고리즘 가중치
            fusion_method: 융합 방법 ('weighted_average', 'max', 'min', 'product')
        """
        super().__init__(**kwargs)

        # 알고리즘 초기화
        if traditional_algorithm is None:
            self.traditional_algo = MFCCSimilarity()
        else:
            self.traditional_algo = traditional_algorithm

        if ai_algorithm is None:
            self.ai_algo = EmbeddingSimilarity()
        else:
            self.ai_algo = ai_algorithm

        # 가중치 정규화
        total_weight = traditional_weight + ai_weight
        self.traditional_weight = traditional_weight / total_weight
        self.ai_weight = ai_weight / total_weight

        self.fusion_method = fusion_method

        logger.info(
            f"HybridSimilarity 초기화: "
            f"traditional={self.traditional_algo.__class__.__name__} ({self.traditional_weight:.2f}), "
            f"ai={self.ai_algo.__class__.__name__} ({self.ai_weight:.2f}), "
            f"fusion={fusion_method}"
        )

    def compute_similarity(
        self,
        target_audio: np.ndarray,
        source_audio: np.ndarray,
        target_sr: int,
        source_sr: int,
    ) -> float:
        """
        두 오디오 간의 하이브리드 유사도 계산

        Args:
            target_audio: 타겟 오디오
            source_audio: 소스 오디오
            target_sr: 타겟 샘플링 레이트
            source_sr: 소스 샘플링 레이트

        Returns:
            유사도 (0~1)
        """
        self._validate_audio(target_audio, target_sr, "target_audio")
        self._validate_audio(source_audio, source_sr, "source_audio")

        # 전통적 알고리즘 유사도
        trad_sim = self.traditional_algo.compute_similarity(
            target_audio, source_audio, target_sr, source_sr
        )

        # AI 알고리즘 유사도
        ai_sim = self.ai_algo.compute_similarity(
            target_audio, source_audio, target_sr, source_sr
        )

        # 융합
        hybrid_sim = self._fuse_scores(trad_sim, ai_sim)

        logger.debug(
            f"하이브리드 유사도: trad={trad_sim:.3f}, ai={ai_sim:.3f}, "
            f"hybrid={hybrid_sim:.3f}"
        )

        return float(hybrid_sim)

    def find_similar_segments(
        self,
        target_audio: np.ndarray,
        source_audio: np.ndarray,
        target_sr: int,
        source_sr: int,
        top_k: int = 10,
    ) -> List[SimilarityMatch]:
        """
        유사한 세그먼트 찾기 (하이브리드)

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

        logger.info("하이브리드 세그먼트 검색 시작...")

        # 전통적 알고리즘으로 후보 찾기
        logger.info("전통적 알고리즘으로 후보 검색 중...")
        trad_matches = self.traditional_algo.find_similar_segments(
            target_audio,
            source_audio,
            target_sr,
            source_sr,
            top_k=top_k * 3,  # 더 많은 후보 생성
        )

        # AI 알고리즘으로 후보 찾기
        logger.info("AI 알고리즘으로 후보 검색 중...")
        ai_matches = self.ai_algo.find_similar_segments(
            target_audio,
            source_audio,
            target_sr,
            source_sr,
            top_k=top_k * 3,
        )

        # 두 결과 결합
        logger.info("결과 융합 중...")
        hybrid_matches = self._merge_matches(trad_matches, ai_matches)

        # 필터링 및 정렬
        hybrid_matches = self._filter_matches(hybrid_matches, top_k=top_k)

        logger.info(f"{len(hybrid_matches)}개의 하이브리드 매치 발견")

        return hybrid_matches

    def _fuse_scores(self, score1: float, score2: float) -> float:
        """
        두 점수를 융합

        Args:
            score1: 첫 번째 점수
            score2: 두 번째 점수

        Returns:
            융합된 점수
        """
        if self.fusion_method == "weighted_average":
            return self.traditional_weight * score1 + self.ai_weight * score2
        elif self.fusion_method == "max":
            return max(score1, score2)
        elif self.fusion_method == "min":
            return min(score1, score2)
        elif self.fusion_method == "product":
            # 기하 평균
            return (score1 * score2) ** 0.5
        else:
            raise ValueError(f"지원하지 않는 융합 방법: {self.fusion_method}")

    def _merge_matches(
        self,
        trad_matches: List[SimilarityMatch],
        ai_matches: List[SimilarityMatch],
    ) -> List[SimilarityMatch]:
        """
        두 매치 리스트를 병합

        시간적으로 가까운 매치들을 그룹화하고 점수를 융합합니다.

        Args:
            trad_matches: 전통적 알고리즘 매치
            ai_matches: AI 알고리즘 매치

        Returns:
            병합된 매치 리스트
        """
        # 모든 매치를 합침
        all_matches = []

        # 전통적 매치에 메타데이터 추가
        for match in trad_matches:
            match.metadata = match.metadata or {}
            match.metadata["source"] = "traditional"
            all_matches.append(match)

        # AI 매치에 메타데이터 추가
        for match in ai_matches:
            match.metadata = match.metadata or {}
            match.metadata["source"] = "ai"
            all_matches.append(match)

        # 시간으로 정렬
        all_matches.sort(key=lambda m: m.source_start)

        # 가까운 매치들 그룹화 및 융합
        merged = []
        time_tolerance = 1.0  # 1초 이내의 매치는 같은 것으로 간주

        i = 0
        while i < len(all_matches):
            current_match = all_matches[i]
            group = [current_match]

            # 가까운 매치 수집
            j = i + 1
            while j < len(all_matches):
                next_match = all_matches[j]
                time_diff = abs(next_match.source_start - current_match.source_start)

                if time_diff <= time_tolerance:
                    group.append(next_match)
                    j += 1
                else:
                    break

            # 그룹 융합
            if len(group) > 1:
                merged_match = self._fuse_match_group(group)
            else:
                merged_match = group[0]

            merged.append(merged_match)
            i = j

        return merged

    def _fuse_match_group(
        self, matches: List[SimilarityMatch]
    ) -> SimilarityMatch:
        """
        매치 그룹을 하나로 융합

        Args:
            matches: 매치 리스트

        Returns:
            융합된 매치
        """
        # 전통적 점수와 AI 점수 분리
        trad_scores = [
            m.similarity for m in matches if m.metadata.get("source") == "traditional"
        ]
        ai_scores = [
            m.similarity for m in matches if m.metadata.get("source") == "ai"
        ]

        # 평균 점수 계산
        trad_score = np.mean(trad_scores) if trad_scores else 0.0
        ai_score = np.mean(ai_scores) if ai_scores else 0.0

        # 융합 점수
        if trad_scores and ai_scores:
            # 둘 다 있으면 융합
            fused_score = self._fuse_scores(trad_score, ai_score)
        elif trad_scores:
            # 전통적만 있으면 그 점수 사용
            fused_score = trad_score
        else:
            # AI만 있으면 그 점수 사용
            fused_score = ai_score

        # 시간 범위는 모든 매치의 평균
        avg_start = np.mean([m.source_start for m in matches])
        avg_end = np.mean([m.source_end for m in matches])

        # 타겟 시간도 평균
        target_start = np.mean([m.target_start for m in matches])
        target_end = np.mean([m.target_end for m in matches])

        # 융합된 매치 생성
        fused_match = SimilarityMatch(
            target_start=target_start,
            target_end=target_end,
            source_start=avg_start,
            source_end=avg_end,
            similarity=fused_score,
            confidence=fused_score,
            metadata={
                "algorithm": "hybrid",
                "fusion_method": self.fusion_method,
                "num_fused": len(matches),
                "traditional_score": trad_score,
                "ai_score": ai_score,
                "has_traditional": len(trad_scores) > 0,
                "has_ai": len(ai_scores) > 0,
            },
        )

        return fused_match

    def __repr__(self) -> str:
        return (
            f"HybridSimilarity("
            f"trad={self.traditional_algo.__class__.__name__}, "
            f"ai={self.ai_algo.__class__.__name__}, "
            f"fusion={self.fusion_method})"
        )
