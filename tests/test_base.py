"""
Tests for Base Similarity Algorithm
"""

import pytest
import numpy as np

from algorithms.base import BaseSimilarityAlgorithm, SimilarityMatch


class DummySimilarityAlgorithm(BaseSimilarityAlgorithm):
    """테스트용 더미 알고리즘"""

    def compute_similarity(self, target_audio, source_audio, target_sr, source_sr):
        return 0.8

    def find_similar_segments(self, target_audio, source_audio, target_sr, source_sr, top_k=10):
        # 3개의 더미 매치 생성
        matches = [
            SimilarityMatch(0.0, 1.0, 0.0, 1.0, 0.9, 0.95),
            SimilarityMatch(0.0, 1.0, 2.0, 3.0, 0.8, 0.85),
            SimilarityMatch(0.0, 1.0, 4.0, 5.0, 0.7, 0.75),
        ]
        return self._filter_matches(matches, top_k)


class TestSimilarityMatch:
    """SimilarityMatch 데이터 클래스 테스트"""

    def test_init(self):
        """초기화 테스트"""
        match = SimilarityMatch(
            target_start=0.0,
            target_end=1.0,
            source_start=2.0,
            source_end=3.0,
            similarity=0.8,
            confidence=0.9,
        )

        assert match.target_start == 0.0
        assert match.target_end == 1.0
        assert match.source_start == 2.0
        assert match.source_end == 3.0
        assert match.similarity == 0.8
        assert match.confidence == 0.9

    def test_duration_properties(self):
        """길이 속성 테스트"""
        match = SimilarityMatch(
            target_start=0.0,
            target_end=2.5,
            source_start=1.0,
            source_end=4.0,
            similarity=0.8,
        )

        assert match.target_duration == 2.5
        assert match.source_duration == 3.0

    def test_repr(self):
        """문자열 표현 테스트"""
        match = SimilarityMatch(0.0, 1.0, 2.0, 3.0, 0.8, 0.9)
        repr_str = repr(match)

        assert "SimilarityMatch" in repr_str
        assert "0.80" in repr_str or "0.800" in repr_str


class TestBaseSimilarityAlgorithm:
    """BaseSimilarityAlgorithm 테스트"""

    def test_init(self):
        """초기화 테스트"""
        algo = DummySimilarityAlgorithm(
            similarity_threshold=0.7,
            confidence_threshold=0.5,
            segment_min_length=0.1,
            segment_max_length=10.0,
        )

        assert algo.similarity_threshold == 0.7
        assert algo.confidence_threshold == 0.5
        assert algo.segment_min_length == 0.1
        assert algo.segment_max_length == 10.0

    def test_validate_audio_valid(self, sample_audio_mono):
        """유효한 오디오 검증 테스트"""
        algo = DummySimilarityAlgorithm()
        audio_data, sample_rate = sample_audio_mono

        # 예외 발생하지 않아야 함
        algo._validate_audio(audio_data, sample_rate, "test_audio")

    def test_validate_audio_empty(self):
        """빈 오디오 검증 테스트"""
        algo = DummySimilarityAlgorithm()

        with pytest.raises(ValueError, match="비어있습니다"):
            algo._validate_audio(np.array([]), 22050, "test_audio")

    def test_validate_audio_invalid_sr(self, sample_audio_mono):
        """잘못된 샘플링 레이트 검증 테스트"""
        algo = DummySimilarityAlgorithm()
        audio_data, _ = sample_audio_mono

        with pytest.raises(ValueError, match="샘플링 레이트"):
            algo._validate_audio(audio_data, -1, "test_audio")

    def test_validate_audio_too_short(self):
        """너무 짧은 오디오 검증 테스트"""
        algo = DummySimilarityAlgorithm(segment_min_length=1.0)

        # 0.05초 오디오 (너무 짧음)
        short_audio = np.random.randn(int(0.05 * 22050)).astype(np.float32)

        with pytest.raises(ValueError, match="최소 세그먼트 길이"):
            algo._validate_audio(short_audio, 22050, "test_audio")

    def test_filter_matches_threshold(self):
        """임계값 필터링 테스트"""
        algo = DummySimilarityAlgorithm(
            similarity_threshold=0.75,
            confidence_threshold=0.8,
        )

        matches = [
            SimilarityMatch(0.0, 1.0, 0.0, 1.0, 0.9, 0.95),  # 통과
            SimilarityMatch(0.0, 1.0, 2.0, 3.0, 0.7, 0.85),  # similarity 낮음
            SimilarityMatch(0.0, 1.0, 4.0, 5.0, 0.8, 0.7),   # confidence 낮음
        ]

        filtered = algo._filter_matches(matches)

        assert len(filtered) == 1
        assert filtered[0].similarity == 0.9

    def test_filter_matches_top_k(self):
        """top_k 제한 테스트"""
        algo = DummySimilarityAlgorithm(similarity_threshold=0.0)

        matches = [
            SimilarityMatch(0.0, 1.0, i, i+1, 0.9 - i*0.1, 0.9)
            for i in range(10)
        ]

        filtered = algo._filter_matches(matches, top_k=3)

        assert len(filtered) == 3
        # 유사도 높은 순 확인
        assert filtered[0].similarity >= filtered[1].similarity
        assert filtered[1].similarity >= filtered[2].similarity

    def test_filter_matches_sorting(self):
        """정렬 테스트"""
        algo = DummySimilarityAlgorithm(similarity_threshold=0.0)

        matches = [
            SimilarityMatch(0.0, 1.0, 0.0, 1.0, 0.7, 0.9),
            SimilarityMatch(0.0, 1.0, 2.0, 3.0, 0.9, 0.9),
            SimilarityMatch(0.0, 1.0, 4.0, 5.0, 0.8, 0.9),
        ]

        filtered = algo._filter_matches(matches)

        # 유사도 내림차순 정렬 확인
        assert filtered[0].similarity == 0.9
        assert filtered[1].similarity == 0.8
        assert filtered[2].similarity == 0.7

    def test_get_name(self):
        """알고리즘 이름 반환 테스트"""
        algo = DummySimilarityAlgorithm()
        assert algo.get_name() == "DummySimilarityAlgorithm"

    def test_get_config(self):
        """설정 반환 테스트"""
        algo = DummySimilarityAlgorithm(
            similarity_threshold=0.7,
            custom_param="test",
        )

        config = algo.get_config()

        assert config['algorithm'] == "DummySimilarityAlgorithm"
        assert config['similarity_threshold'] == 0.7
        assert config['custom_param'] == "test"

    def test_repr(self):
        """문자열 표현 테스트"""
        algo = DummySimilarityAlgorithm(similarity_threshold=0.75)
        repr_str = repr(algo)

        assert "DummySimilarityAlgorithm" in repr_str
        assert "0.75" in repr_str

    def test_compute_similarity(self, sample_audio_mono):
        """유사도 계산 테스트"""
        algo = DummySimilarityAlgorithm()
        audio_data, sample_rate = sample_audio_mono

        similarity = algo.compute_similarity(
            audio_data, audio_data, sample_rate, sample_rate
        )

        assert isinstance(similarity, float)
        assert 0.0 <= similarity <= 1.0

    def test_find_similar_segments(self, sample_audio_mono):
        """유사 세그먼트 찾기 테스트"""
        algo = DummySimilarityAlgorithm(similarity_threshold=0.0)
        audio_data, sample_rate = sample_audio_mono

        # 더 긴 소스 오디오 생성
        source_audio = np.random.randn(len(audio_data) * 3).astype(np.float32)

        matches = algo.find_similar_segments(
            audio_data, source_audio, sample_rate, sample_rate, top_k=5
        )

        assert isinstance(matches, list)
        assert len(matches) <= 5
        for match in matches:
            assert isinstance(match, SimilarityMatch)
