"""
Tests for Similarity Algorithms
"""

import pytest
import numpy as np

from algorithms.traditional.mfcc import MFCCSimilarity
from algorithms.traditional.spectral import SpectralSimilarity
from algorithms.traditional.energy import EnergySimilarity
from algorithms.traditional.rhythm import RhythmSimilarity
from algorithms.random.random_matcher import RandomMatcher


class TestMFCCSimilarity:
    """MFCC 기반 유사도 알고리즘 테스트"""

    def test_init(self):
        """초기화 테스트"""
        algo = MFCCSimilarity(
            n_mfcc=13,
            n_fft=2048,
            hop_length=512,
            distance_metric='euclidean',
        )

        assert algo.n_mfcc == 13
        assert algo.n_fft == 2048
        assert algo.hop_length == 512
        assert algo.distance_metric == 'euclidean'

    def test_extract_mfcc(self, sample_audio_mono):
        """MFCC 추출 테스트"""
        algo = MFCCSimilarity(n_mfcc=13)
        audio_data, sample_rate = sample_audio_mono

        mfcc = algo._extract_mfcc(audio_data, sample_rate)

        assert mfcc.ndim == 2
        assert mfcc.shape[0] == 13  # n_mfcc
        assert mfcc.shape[1] > 0

    def test_extract_mfcc_with_delta(self, sample_audio_mono):
        """Delta MFCC 추출 테스트"""
        algo = MFCCSimilarity(n_mfcc=13, use_delta=True, use_delta_delta=True)
        audio_data, sample_rate = sample_audio_mono

        mfcc = algo._extract_mfcc(audio_data, sample_rate)

        # MFCC + Delta + Delta-Delta = 13 * 3 = 39
        assert mfcc.shape[0] == 39

    def test_compute_distance_euclidean(self, sample_audio_mono):
        """유클리드 거리 계산 테스트"""
        algo = MFCCSimilarity(distance_metric='euclidean')
        audio_data, sample_rate = sample_audio_mono

        mfcc1 = algo._extract_mfcc(audio_data, sample_rate)
        mfcc2 = algo._extract_mfcc(audio_data, sample_rate)

        distance = algo._compute_distance(mfcc1, mfcc2)

        assert isinstance(distance, float)
        assert distance >= 0.0
        # 동일한 오디오이므로 거리가 매우 작아야 함
        assert distance < 1.0

    def test_compute_distance_cosine(self, sample_audio_mono):
        """코사인 거리 계산 테스트"""
        algo = MFCCSimilarity(distance_metric='cosine')
        audio_data, sample_rate = sample_audio_mono

        mfcc = algo._extract_mfcc(audio_data, sample_rate)
        distance = algo._compute_distance(mfcc, mfcc)

        assert isinstance(distance, float)
        assert distance >= 0.0

    def test_compute_similarity(self, sample_audio_mono):
        """유사도 계산 테스트"""
        algo = MFCCSimilarity()
        audio_data, sample_rate = sample_audio_mono

        similarity = algo.compute_similarity(
            audio_data, audio_data, sample_rate, sample_rate
        )

        assert 0.0 <= similarity <= 1.0
        # 동일한 오디오이므로 유사도가 높아야 함
        assert similarity > 0.5

    def test_find_similar_segments(self, sample_audio_mono):
        """유사 세그먼트 찾기 테스트"""
        algo = MFCCSimilarity(similarity_threshold=0.0)
        audio_data, sample_rate = sample_audio_mono

        # 소스 오디오는 타겟을 3번 반복
        source_audio = np.tile(audio_data, 3)

        matches = algo.find_similar_segments(
            audio_data, source_audio, sample_rate, sample_rate, top_k=5
        )

        assert isinstance(matches, list)
        assert len(matches) > 0
        # 유사도 정렬 확인
        for i in range(len(matches) - 1):
            assert matches[i].similarity >= matches[i+1].similarity


class TestSpectralSimilarity:
    """스펙트럼 기반 유사도 알고리즘 테스트"""

    def test_init(self):
        """초기화 테스트"""
        algo = SpectralSimilarity(
            centroid_weight=0.3,
            rolloff_weight=0.3,
        )

        # 가중치가 정규화되었는지 확인
        total = (algo.centroid_weight + algo.rolloff_weight +
                algo.contrast_weight + algo.bandwidth_weight)
        assert abs(total - 1.0) < 1e-6

    def test_extract_spectral_features(self, sample_audio_mono):
        """스펙트럼 특징 추출 테스트"""
        algo = SpectralSimilarity()
        audio_data, sample_rate = sample_audio_mono

        features = algo._extract_spectral_features(audio_data, sample_rate)

        assert 'centroid' in features
        assert 'rolloff' in features
        assert 'contrast' in features
        assert 'bandwidth' in features

        assert len(features['centroid']) > 0
        assert features['contrast'].ndim == 2

    def test_compute_feature_similarity(self, sample_audio_mono):
        """특징 유사도 계산 테스트"""
        algo = SpectralSimilarity()
        audio_data, sample_rate = sample_audio_mono

        features = algo._extract_spectral_features(audio_data, sample_rate)

        similarity = algo._compute_feature_similarity(
            features['centroid'], features['centroid']
        )

        assert 0.0 <= similarity <= 1.0
        # 동일한 특징이므로 유사도가 높아야 함
        assert similarity > 0.8

    def test_compute_similarity(self, sample_audio_mono):
        """유사도 계산 테스트"""
        algo = SpectralSimilarity()
        audio_data, sample_rate = sample_audio_mono

        similarity = algo.compute_similarity(
            audio_data, audio_data, sample_rate, sample_rate
        )

        assert 0.0 <= similarity <= 1.0

    def test_find_similar_segments(self, sample_audio_mono):
        """유사 세그먼트 찾기 테스트"""
        algo = SpectralSimilarity(similarity_threshold=0.0)
        audio_data, sample_rate = sample_audio_mono
        source_audio = np.random.randn(len(audio_data) * 3).astype(np.float32)

        matches = algo.find_similar_segments(
            audio_data, source_audio, sample_rate, sample_rate, top_k=5
        )

        assert isinstance(matches, list)


class TestEnergySimilarity:
    """에너지 기반 유사도 알고리즘 테스트"""

    def test_init(self):
        """초기화 테스트"""
        algo = EnergySimilarity(
            frame_length=2048,
            normalize_energy=True,
        )

        assert algo.frame_length == 2048
        assert algo.normalize_energy is True

    def test_extract_energy(self, sample_audio_mono):
        """에너지 추출 테스트"""
        algo = EnergySimilarity()
        audio_data, _ = sample_audio_mono

        energy = algo._extract_energy(audio_data)

        assert energy.ndim == 1
        assert len(energy) > 0
        assert np.all(np.isfinite(energy))

    def test_extract_energy_normalized(self, sample_audio_mono):
        """정규화된 에너지 추출 테스트"""
        algo = EnergySimilarity(normalize_energy=True)
        audio_data, _ = sample_audio_mono

        energy = algo._extract_energy(audio_data)

        # 정규화된 경우 평균이 0에 가까워야 함
        assert abs(np.mean(energy)) < 1.0

    def test_compute_similarity(self, sample_audio_mono):
        """유사도 계산 테스트"""
        algo = EnergySimilarity()
        audio_data, sample_rate = sample_audio_mono

        similarity = algo.compute_similarity(
            audio_data, audio_data, sample_rate, sample_rate
        )

        assert 0.0 <= similarity <= 1.0
        # 동일한 오디오이므로 유사도가 높아야 함
        assert similarity > 0.8

    def test_find_similar_segments(self, sample_audio_mono):
        """유사 세그먼트 찾기 테스트"""
        algo = EnergySimilarity(similarity_threshold=0.0)
        audio_data, sample_rate = sample_audio_mono
        source_audio = np.tile(audio_data, 2)

        matches = algo.find_similar_segments(
            audio_data, source_audio, sample_rate, sample_rate, top_k=3
        )

        assert isinstance(matches, list)


class TestRhythmSimilarity:
    """리듬 기반 유사도 알고리즘 테스트"""

    def test_init(self):
        """초기화 테스트"""
        algo = RhythmSimilarity(use_tempo=True, use_onset=True)

        assert algo.use_tempo is True
        assert algo.use_onset is True

    def test_extract_rhythm_features(self, sample_audio_mono):
        """리듬 특징 추출 테스트"""
        algo = RhythmSimilarity()
        audio_data, sample_rate = sample_audio_mono

        features = algo._extract_rhythm_features(audio_data, sample_rate)

        if algo.use_tempo:
            assert 'tempo' in features
            assert 'beats' in features
            assert features['tempo'] > 0

        if algo.use_onset:
            assert 'onset_env' in features
            assert len(features['onset_env']) > 0

    def test_compute_similarity(self, sample_audio_mono):
        """유사도 계산 테스트"""
        algo = RhythmSimilarity()
        audio_data, sample_rate = sample_audio_mono

        similarity = algo.compute_similarity(
            audio_data, audio_data, sample_rate, sample_rate
        )

        assert 0.0 <= similarity <= 1.0

    def test_find_similar_segments(self, sample_audio_mono):
        """유사 세그먼트 찾기 테스트"""
        algo = RhythmSimilarity(similarity_threshold=0.0)
        audio_data, sample_rate = sample_audio_mono
        source_audio = np.random.randn(len(audio_data) * 3).astype(np.float32)

        matches = algo.find_similar_segments(
            audio_data, source_audio, sample_rate, sample_rate, top_k=3
        )

        assert isinstance(matches, list)


class TestRandomMatcher:
    """랜덤 매칭 알고리즘 테스트"""

    def test_init(self):
        """초기화 테스트"""
        algo = RandomMatcher(seed=42, weighted=False)

        assert algo.seed == 42
        assert algo.weighted is False

    def test_compute_similarity(self, sample_audio_mono):
        """유사도 계산 테스트"""
        algo = RandomMatcher(seed=42)
        audio_data, sample_rate = sample_audio_mono

        similarity = algo.compute_similarity(
            audio_data, audio_data, sample_rate, sample_rate
        )

        assert 0.0 <= similarity <= 1.0

    def test_compute_similarity_deterministic(self, sample_audio_mono):
        """결정론적 동작 테스트 (같은 시드)"""
        algo1 = RandomMatcher(seed=42)
        algo2 = RandomMatcher(seed=42)
        audio_data, sample_rate = sample_audio_mono

        sim1 = algo1.compute_similarity(audio_data, audio_data, sample_rate, sample_rate)
        sim2 = algo2.compute_similarity(audio_data, audio_data, sample_rate, sample_rate)

        assert sim1 == sim2

    def test_find_similar_segments(self, sample_audio_mono):
        """유사 세그먼트 찾기 테스트"""
        algo = RandomMatcher(seed=42)
        audio_data, sample_rate = sample_audio_mono
        source_audio = np.random.randn(len(audio_data) * 5).astype(np.float32)

        matches = algo.find_similar_segments(
            audio_data, source_audio, sample_rate, sample_rate, top_k=5
        )

        assert isinstance(matches, list)
        assert len(matches) <= 5

    def test_find_similar_segments_weighted(self, sample_audio_mono):
        """가중치 기반 랜덤 매칭 테스트"""
        algo = RandomMatcher(seed=42, weighted=True)
        audio_data, sample_rate = sample_audio_mono
        source_audio = np.random.randn(len(audio_data) * 5).astype(np.float32)

        matches = algo.find_similar_segments(
            audio_data, source_audio, sample_rate, sample_rate, top_k=5
        )

        assert isinstance(matches, list)
        assert len(matches) <= 5

    def test_find_similar_segments_deterministic(self, sample_audio_mono):
        """결정론적 세그먼트 찾기 테스트"""
        algo1 = RandomMatcher(seed=42)
        algo2 = RandomMatcher(seed=42)
        audio_data, sample_rate = sample_audio_mono
        source_audio = np.random.randn(len(audio_data) * 5).astype(np.float32)

        matches1 = algo1.find_similar_segments(
            audio_data, source_audio, sample_rate, sample_rate, top_k=3
        )
        matches2 = algo2.find_similar_segments(
            audio_data, source_audio, sample_rate, sample_rate, top_k=3
        )

        # 같은 시드면 같은 결과
        assert len(matches1) == len(matches2)
        for m1, m2 in zip(matches1, matches2):
            assert abs(m1.source_start - m2.source_start) < 1e-6
