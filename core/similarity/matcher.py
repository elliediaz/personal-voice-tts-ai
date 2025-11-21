"""
Segment Matching Module

세그먼트 매칭 및 최적화 기능을 제공합니다.
"""

from typing import List, Optional
import numpy as np

from algorithms.base import SimilarityMatch
from utils.logging import get_logger

logger = get_logger(__name__)


class SegmentMatcher:
    """
    세그먼트 매칭 및 후처리를 담당하는 클래스.
    """

    def __init__(
        self,
        overlap_threshold: float = 0.5,
        min_segment_gap: float = 0.1,
    ):
        """
        SegmentMatcher를 초기화합니다.

        Args:
            overlap_threshold: 오버랩 제거 임계값 (0.0 ~ 1.0)
            min_segment_gap: 최소 세그먼트 간격 (초)
        """
        self.overlap_threshold = overlap_threshold
        self.min_segment_gap = min_segment_gap

    def remove_overlaps(
        self,
        matches: List[SimilarityMatch],
        mode: str = 'source',
    ) -> List[SimilarityMatch]:
        """
        오버랩되는 매치를 제거합니다.

        Args:
            matches: 매칭 결과 리스트
            mode: 'source' 또는 'target' - 어느 쪽을 기준으로 오버랩 제거할지

        Returns:
            List[SimilarityMatch]: 오버랩이 제거된 매칭 결과
        """
        if not matches:
            return []

        # 유사도 기준 정렬 (높은 순)
        sorted_matches = sorted(matches, key=lambda x: x.similarity, reverse=True)

        filtered = []

        for match in sorted_matches:
            is_overlapping = False

            for existing in filtered:
                if mode == 'source':
                    overlap = self._compute_overlap(
                        match.source_start, match.source_end,
                        existing.source_start, existing.source_end,
                    )
                else:  # target
                    overlap = self._compute_overlap(
                        match.target_start, match.target_end,
                        existing.target_start, existing.target_end,
                    )

                if overlap > self.overlap_threshold:
                    is_overlapping = True
                    break

            if not is_overlapping:
                filtered.append(match)

        # 원래 순서 (시간 순)로 정렬
        if mode == 'source':
            filtered.sort(key=lambda x: x.source_start)
        else:
            filtered.sort(key=lambda x: x.target_start)

        logger.debug(
            f"오버랩 제거: {len(matches)}개 -> {len(filtered)}개 "
            f"(mode={mode})"
        )

        return filtered

    def _compute_overlap(
        self,
        start1: float,
        end1: float,
        start2: float,
        end2: float,
    ) -> float:
        """
        두 구간의 오버랩 비율을 계산합니다.

        Args:
            start1: 첫 번째 구간 시작
            end1: 첫 번째 구간 종료
            start2: 두 번째 구간 시작
            end2: 두 번째 구간 종료

        Returns:
            float: 오버랩 비율 (0.0 ~ 1.0)
        """
        overlap_start = max(start1, start2)
        overlap_end = min(end1, end2)

        if overlap_end <= overlap_start:
            return 0.0

        overlap_duration = overlap_end - overlap_start
        min_duration = min(end1 - start1, end2 - start2)

        return overlap_duration / min_duration if min_duration > 0 else 0.0

    def merge_close_segments(
        self,
        matches: List[SimilarityMatch],
    ) -> List[SimilarityMatch]:
        """
        가까운 세그먼트들을 병합합니다.

        Args:
            matches: 매칭 결과 리스트

        Returns:
            List[SimilarityMatch]: 병합된 매칭 결과
        """
        if not matches:
            return []

        # 소스 시작 시간 기준 정렬
        sorted_matches = sorted(matches, key=lambda x: x.source_start)

        merged = [sorted_matches[0]]

        for current in sorted_matches[1:]:
            last = merged[-1]

            # 세그먼트 간격 확인
            gap = current.source_start - last.source_end

            if gap < self.min_segment_gap:
                # 병합
                merged[-1] = SimilarityMatch(
                    target_start=min(last.target_start, current.target_start),
                    target_end=max(last.target_end, current.target_end),
                    source_start=min(last.source_start, current.source_start),
                    source_end=max(last.source_end, current.source_end),
                    similarity=max(last.similarity, current.similarity),
                    confidence=min(last.confidence, current.confidence),
                    metadata={'merged': True},
                )
            else:
                merged.append(current)

        logger.debug(f"세그먼트 병합: {len(matches)}개 -> {len(merged)}개")

        return merged

    def rank_matches(
        self,
        matches: List[SimilarityMatch],
        ranking_method: str = 'similarity',
    ) -> List[SimilarityMatch]:
        """
        매칭 결과를 순위화합니다.

        Args:
            matches: 매칭 결과 리스트
            ranking_method: 순위화 방법 ('similarity', 'confidence', 'combined')

        Returns:
            List[SimilarityMatch]: 순위화된 매칭 결과
        """
        if ranking_method == 'similarity':
            key_func = lambda x: x.similarity
        elif ranking_method == 'confidence':
            key_func = lambda x: x.confidence
        elif ranking_method == 'combined':
            key_func = lambda x: (x.similarity + x.confidence) / 2.0
        else:
            raise ValueError(f"지원하지 않는 순위화 방법: {ranking_method}")

        return sorted(matches, key=key_func, reverse=True)

    def filter_by_duration(
        self,
        matches: List[SimilarityMatch],
        min_duration: Optional[float] = None,
        max_duration: Optional[float] = None,
    ) -> List[SimilarityMatch]:
        """
        길이를 기준으로 매칭 결과를 필터링합니다.

        Args:
            matches: 매칭 결과 리스트
            min_duration: 최소 길이 (초)
            max_duration: 최대 길이 (초)

        Returns:
            List[SimilarityMatch]: 필터링된 매칭 결과
        """
        filtered = []

        for match in matches:
            duration = match.source_duration

            if min_duration is not None and duration < min_duration:
                continue

            if max_duration is not None and duration > max_duration:
                continue

            filtered.append(match)

        logger.debug(
            f"길이 필터링: {len(matches)}개 -> {len(filtered)}개 "
            f"(min={min_duration}, max={max_duration})"
        )

        return filtered


__all__ = ["SegmentMatcher"]
