"""
Tests for Algorithm Manager
"""

import pytest
import numpy as np

from core.similarity.manager import AlgorithmManager
from algorithms.traditional.mfcc import MFCCSimilarity
from algorithms.base import SimilarityMatch


class TestAlgorithmManager:
    """AlgorithmManager 테스트"""

    def test_init(self):
        """초기화 테스트"""
        manager = AlgorithmManager()

        # 기본 알고리즘들이 등록되었는지 확인
        algorithms = manager.list_algorithms()

        assert 'mfcc' in algorithms
        assert 'spectral' in algorithms
        assert 'energy' in algorithms
        assert 'rhythm' in algorithms
        assert 'random' in algorithms

    def test_register(self):
        """알고리즘 등록 테스트"""
        manager = AlgorithmManager()

        custom_algo = MFCCSimilarity(n_mfcc=20)
        manager.register('custom_mfcc', custom_algo)

        assert 'custom_mfcc' in manager.list_algorithms()
        assert manager.get_algorithm('custom_mfcc') == custom_algo

    def test_get_algorithm(self):
        """알고리즘 가져오기 테스트"""
        manager = AlgorithmManager()

        mfcc_algo = manager.get_algorithm('mfcc')

        assert mfcc_algo is not None
        assert isinstance(mfcc_algo, MFCCSimilarity)

    def test_get_algorithm_not_found(self):
        """존재하지 않는 알고리즘 테스트"""
        manager = AlgorithmManager()

        algo = manager.get_algorithm('nonexistent')

        assert algo is None

    def test_list_algorithms(self):
        """알고리즘 목록 테스트"""
        manager = AlgorithmManager()

        algorithms = manager.list_algorithms()

        assert isinstance(algorithms, list)
        assert len(algorithms) >= 5  # 최소 5개 기본 알고리즘

    def test_find_similar_segments(self, sample_audio_mono):
        """유사 세그먼트 찾기 테스트"""
        manager = AlgorithmManager()
        audio_data, sample_rate = sample_audio_mono

        # 소스 오디오는 타겟을 반복
        source_audio = np.tile(audio_data, 2)

        matches = manager.find_similar_segments(
            'mfcc',
            audio_data,
            source_audio,
            sample_rate,
            sample_rate,
            top_k=5,
        )

        assert isinstance(matches, list)
        assert len(matches) <= 5

    def test_find_similar_segments_invalid_algorithm(self, sample_audio_mono):
        """잘못된 알고리즘 이름 테스트"""
        manager = AlgorithmManager()
        audio_data, sample_rate = sample_audio_mono

        with pytest.raises(ValueError, match="알고리즘을 찾을 수 없습니다"):
            manager.find_similar_segments(
                'invalid_algo',
                audio_data,
                audio_data,
                sample_rate,
                sample_rate,
            )

    def test_find_similar_segments_with_overlap_removal(self, sample_audio_mono):
        """오버랩 제거 포함 세그먼트 찾기 테스트"""
        manager = AlgorithmManager()
        audio_data, sample_rate = sample_audio_mono
        source_audio = np.tile(audio_data, 3)

        matches_with_removal = manager.find_similar_segments(
            'mfcc',
            audio_data,
            source_audio,
            sample_rate,
            sample_rate,
            top_k=5,
            remove_overlaps=True,
        )

        matches_without_removal = manager.find_similar_segments(
            'mfcc',
            audio_data,
            source_audio,
            sample_rate,
            sample_rate,
            top_k=5,
            remove_overlaps=False,
        )

        # 오버랩 제거 시 결과가 같거나 적어야 함
        assert len(matches_with_removal) <= len(matches_without_removal)

    def test_ensemble_find_segments(self, sample_audio_mono):
        """앙상블 세그먼트 찾기 테스트"""
        manager = AlgorithmManager()
        audio_data, sample_rate = sample_audio_mono
        source_audio = np.random.randn(len(audio_data) * 3).astype(np.float32)

        matches = manager.ensemble_find_segments(
            ['mfcc', 'energy'],
            audio_data,
            source_audio,
            sample_rate,
            sample_rate,
            top_k=3,
        )

        assert isinstance(matches, list)
        assert len(matches) <= 3

        # 앙상블 메타데이터 확인
        if matches:
            assert matches[0].metadata.get('ensemble') is True
            assert 'algorithms' in matches[0].metadata

    def test_ensemble_find_segments_with_weights(self, sample_audio_mono):
        """가중치 포함 앙상블 테스트"""
        manager = AlgorithmManager()
        audio_data, sample_rate = sample_audio_mono
        source_audio = np.random.randn(len(audio_data) * 3).astype(np.float32)

        matches = manager.ensemble_find_segments(
            ['mfcc', 'energy'],
            audio_data,
            source_audio,
            sample_rate,
            sample_rate,
            weights=[0.7, 0.3],
            top_k=3,
        )

        assert isinstance(matches, list)

    def test_ensemble_find_segments_empty_algorithms(self, sample_audio_mono):
        """빈 알고리즘 리스트 테스트"""
        manager = AlgorithmManager()
        audio_data, sample_rate = sample_audio_mono

        with pytest.raises(ValueError, match="최소 하나 이상"):
            manager.ensemble_find_segments(
                [],
                audio_data,
                audio_data,
                sample_rate,
                sample_rate,
            )

    def test_ensemble_find_segments_weight_mismatch(self, sample_audio_mono):
        """가중치 개수 불일치 테스트"""
        manager = AlgorithmManager()
        audio_data, sample_rate = sample_audio_mono

        with pytest.raises(ValueError, match="가중치 개수"):
            manager.ensemble_find_segments(
                ['mfcc', 'energy'],
                audio_data,
                audio_data,
                sample_rate,
                sample_rate,
                weights=[0.5],  # 2개 알고리즘에 1개 가중치
            )

    def test_ensemble_voting_methods(self, sample_audio_mono):
        """다양한 투표 방법 테스트"""
        manager = AlgorithmManager()
        audio_data, sample_rate = sample_audio_mono
        source_audio = np.random.randn(len(audio_data) * 3).astype(np.float32)

        for method in ['weighted_average', 'max', 'min']:
            matches = manager.ensemble_find_segments(
                ['mfcc', 'energy'],
                audio_data,
                source_audio,
                sample_rate,
                sample_rate,
                voting_method=method,
                top_k=2,
            )

            assert isinstance(matches, list)

    def test_ensemble_invalid_voting_method(self, sample_audio_mono):
        """잘못된 투표 방법 테스트"""
        manager = AlgorithmManager()
        audio_data, sample_rate = sample_audio_mono

        with pytest.raises(ValueError, match="투표 방법"):
            manager.ensemble_find_segments(
                ['mfcc'],
                audio_data,
                audio_data,
                sample_rate,
                sample_rate,
                voting_method='invalid',
            )

    def test_group_similar_matches(self):
        """유사 매치 그룹화 테스트"""
        manager = AlgorithmManager()

        matches = [
            SimilarityMatch(0.0, 1.0, 0.0, 1.0, 0.9, 0.9, {'algorithm': 'mfcc'}),
            SimilarityMatch(0.0, 1.0, 0.1, 1.1, 0.8, 0.8, {'algorithm': 'energy'}),  # 가까움
            SimilarityMatch(0.0, 1.0, 5.0, 6.0, 0.7, 0.7, {'algorithm': 'mfcc'}),  # 멀리 떨어짐
        ]

        groups = manager._group_similar_matches(matches, time_tolerance=0.5)

        # 처음 두 개는 그룹화, 세 번째는 별도 그룹
        assert len(groups) == 2
        assert len(groups[0]) == 2
        assert len(groups[1]) == 1

    def test_group_similar_matches_empty(self):
        """빈 리스트 그룹화 테스트"""
        manager = AlgorithmManager()

        groups = manager._group_similar_matches([])

        assert groups == []

    def test_benchmark_algorithms(self):
        """알고리즘 벤치마크 테스트"""
        manager = AlgorithmManager()

        results = manager.benchmark_algorithms(
            algorithm_names=['mfcc', 'energy'],
            test_duration=1.0,  # 짧은 테스트
        )

        assert isinstance(results, dict)
        assert 'mfcc' in results
        assert 'energy' in results

        # 성공한 경우 결과 확인
        for name, result in results.items():
            if result.get('success'):
                assert 'num_matches' in result
                assert 'elapsed_time' in result
                assert 'avg_similarity' in result
                assert result['elapsed_time'] > 0

    def test_benchmark_all_algorithms(self):
        """모든 알고리즘 벤치마크 테스트"""
        manager = AlgorithmManager()

        # 모든 알고리즘 벤치마크 (None으로 지정)
        results = manager.benchmark_algorithms(
            algorithm_names=None,
            test_duration=0.5,  # 매우 짧은 테스트
        )

        # 모든 기본 알고리즘이 포함되어야 함
        assert len(results) >= 5

    def test_benchmark_with_custom_audio(self, sample_audio_mono):
        """커스텀 오디오로 벤치마크 테스트"""
        manager = AlgorithmManager()
        audio_data, sample_rate = sample_audio_mono
        source_audio = np.tile(audio_data, 2)

        results = manager.benchmark_algorithms(
            algorithm_names=['mfcc'],
            target_audio=audio_data,
            source_audio=source_audio,
            target_sr=sample_rate,
            source_sr=sample_rate,
        )

        assert 'mfcc' in results
        assert results['mfcc'].get('success') is True
