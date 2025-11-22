"""
Tests for Segment Matcher
"""

import pytest

from algorithms.base import SimilarityMatch
from core.similarity.matcher import SegmentMatcher


class TestSegmentMatcher:
    """SegmentMatcher 테스트"""

    def test_init(self):
        """초기화 테스트"""
        matcher = SegmentMatcher(
            overlap_threshold=0.5,
            min_segment_gap=0.1,
        )

        assert matcher.overlap_threshold == 0.5
        assert matcher.min_segment_gap == 0.1

    def test_compute_overlap_no_overlap(self):
        """오버랩 없는 경우 테스트"""
        matcher = SegmentMatcher()

        overlap = matcher._compute_overlap(0.0, 1.0, 2.0, 3.0)

        assert overlap == 0.0

    def test_compute_overlap_partial(self):
        """부분 오버랩 테스트"""
        matcher = SegmentMatcher()

        overlap = matcher._compute_overlap(0.0, 2.0, 1.0, 3.0)

        # 1.0 ~ 2.0 구간이 오버랩 (길이 1.0)
        # 짧은 구간 길이는 2.0
        assert overlap == 0.5  # 1.0 / 2.0

    def test_compute_overlap_complete(self):
        """완전 오버랩 테스트"""
        matcher = SegmentMatcher()

        overlap = matcher._compute_overlap(0.0, 2.0, 0.5, 1.5)

        # 0.5 ~ 1.5 구간이 완전히 포함 (길이 1.0)
        assert overlap == 1.0  # 1.0 / 1.0

    def test_remove_overlaps_source(self):
        """소스 기준 오버랩 제거 테스트"""
        matcher = SegmentMatcher(overlap_threshold=0.3)

        matches = [
            SimilarityMatch(0.0, 1.0, 0.0, 1.0, 0.9, 0.9),   # 높은 유사도
            SimilarityMatch(0.0, 1.0, 0.5, 1.5, 0.8, 0.8),   # 오버랩
            SimilarityMatch(0.0, 1.0, 3.0, 4.0, 0.7, 0.7),   # 오버랩 없음
        ]

        filtered = matcher.remove_overlaps(matches, mode='source')

        # 첫 번째와 세 번째만 남아야 함 (두 번째는 첫 번째와 오버랩)
        assert len(filtered) == 2
        assert filtered[0].source_start == 0.0
        assert filtered[1].source_start == 3.0

    def test_remove_overlaps_target(self):
        """타겟 기준 오버랩 제거 테스트"""
        matcher = SegmentMatcher(overlap_threshold=0.3)

        matches = [
            SimilarityMatch(0.0, 1.0, 0.0, 1.0, 0.9, 0.9),
            SimilarityMatch(0.5, 1.5, 2.0, 3.0, 0.8, 0.8),
            SimilarityMatch(3.0, 4.0, 4.0, 5.0, 0.7, 0.7),
        ]

        filtered = matcher.remove_overlaps(matches, mode='target')

        assert len(filtered) == 2

    def test_remove_overlaps_empty(self):
        """빈 리스트 테스트"""
        matcher = SegmentMatcher()

        filtered = matcher.remove_overlaps([], mode='source')

        assert filtered == []

    def test_merge_close_segments(self):
        """가까운 세그먼트 병합 테스트"""
        matcher = SegmentMatcher(min_segment_gap=0.2)

        matches = [
            SimilarityMatch(0.0, 1.0, 0.0, 1.0, 0.9, 0.9),
            SimilarityMatch(0.0, 1.0, 1.05, 2.0, 0.8, 0.8),  # 간격 0.05초
            SimilarityMatch(0.0, 1.0, 3.0, 4.0, 0.7, 0.7),   # 간격 1.0초
        ]

        merged = matcher.merge_close_segments(matches)

        # 첫 두 개가 병합되어야 함
        assert len(merged) == 2
        assert merged[0].source_start == 0.0
        assert merged[0].source_end == 2.0
        assert merged[1].source_start == 3.0

    def test_merge_close_segments_empty(self):
        """빈 리스트 병합 테스트"""
        matcher = SegmentMatcher()

        merged = matcher.merge_close_segments([])

        assert merged == []

    def test_rank_matches_by_similarity(self):
        """유사도 기준 순위화 테스트"""
        matcher = SegmentMatcher()

        matches = [
            SimilarityMatch(0.0, 1.0, 0.0, 1.0, 0.7, 0.9),
            SimilarityMatch(0.0, 1.0, 2.0, 3.0, 0.9, 0.8),
            SimilarityMatch(0.0, 1.0, 4.0, 5.0, 0.8, 0.7),
        ]

        ranked = matcher.rank_matches(matches, ranking_method='similarity')

        assert ranked[0].similarity == 0.9
        assert ranked[1].similarity == 0.8
        assert ranked[2].similarity == 0.7

    def test_rank_matches_by_confidence(self):
        """신뢰도 기준 순위화 테스트"""
        matcher = SegmentMatcher()

        matches = [
            SimilarityMatch(0.0, 1.0, 0.0, 1.0, 0.7, 0.7),
            SimilarityMatch(0.0, 1.0, 2.0, 3.0, 0.8, 0.9),
            SimilarityMatch(0.0, 1.0, 4.0, 5.0, 0.9, 0.8),
        ]

        ranked = matcher.rank_matches(matches, ranking_method='confidence')

        assert ranked[0].confidence == 0.9
        assert ranked[1].confidence == 0.8
        assert ranked[2].confidence == 0.7

    def test_rank_matches_by_combined(self):
        """결합 점수 기준 순위화 테스트"""
        matcher = SegmentMatcher()

        matches = [
            SimilarityMatch(0.0, 1.0, 0.0, 1.0, 0.8, 0.6),  # avg 0.7
            SimilarityMatch(0.0, 1.0, 2.0, 3.0, 0.7, 0.9),  # avg 0.8
            SimilarityMatch(0.0, 1.0, 4.0, 5.0, 0.9, 0.8),  # avg 0.85
        ]

        ranked = matcher.rank_matches(matches, ranking_method='combined')

        # 결합 점수가 높은 순
        assert ranked[0].source_start == 4.0  # 0.85
        assert ranked[1].source_start == 2.0  # 0.8
        assert ranked[2].source_start == 0.0  # 0.7

    def test_rank_matches_invalid_method(self):
        """잘못된 순위화 방법 테스트"""
        matcher = SegmentMatcher()
        matches = [SimilarityMatch(0.0, 1.0, 0.0, 1.0, 0.8, 0.8)]

        with pytest.raises(ValueError, match="순위화 방법"):
            matcher.rank_matches(matches, ranking_method='invalid')

    def test_filter_by_duration_min(self):
        """최소 길이 필터링 테스트"""
        matcher = SegmentMatcher()

        matches = [
            SimilarityMatch(0.0, 1.0, 0.0, 0.5, 0.9, 0.9),   # 0.5초
            SimilarityMatch(0.0, 1.0, 1.0, 2.5, 0.8, 0.8),   # 1.5초
            SimilarityMatch(0.0, 1.0, 3.0, 5.0, 0.7, 0.7),   # 2.0초
        ]

        filtered = matcher.filter_by_duration(matches, min_duration=1.0)

        assert len(filtered) == 2
        assert filtered[0].source_duration >= 1.0
        assert filtered[1].source_duration >= 1.0

    def test_filter_by_duration_max(self):
        """최대 길이 필터링 테스트"""
        matcher = SegmentMatcher()

        matches = [
            SimilarityMatch(0.0, 1.0, 0.0, 0.5, 0.9, 0.9),   # 0.5초
            SimilarityMatch(0.0, 1.0, 1.0, 2.5, 0.8, 0.8),   # 1.5초
            SimilarityMatch(0.0, 1.0, 3.0, 5.0, 0.7, 0.7),   # 2.0초
        ]

        filtered = matcher.filter_by_duration(matches, max_duration=1.5)

        assert len(filtered) == 2
        assert filtered[0].source_duration <= 1.5
        assert filtered[1].source_duration <= 1.5

    def test_filter_by_duration_range(self):
        """길이 범위 필터링 테스트"""
        matcher = SegmentMatcher()

        matches = [
            SimilarityMatch(0.0, 1.0, 0.0, 0.5, 0.9, 0.9),   # 0.5초
            SimilarityMatch(0.0, 1.0, 1.0, 2.5, 0.8, 0.8),   # 1.5초
            SimilarityMatch(0.0, 1.0, 3.0, 5.0, 0.7, 0.7),   # 2.0초
        ]

        filtered = matcher.filter_by_duration(
            matches,
            min_duration=1.0,
            max_duration=1.8,
        )

        assert len(filtered) == 1
        assert filtered[0].source_duration == 1.5
