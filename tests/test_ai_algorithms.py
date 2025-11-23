"""
Tests for AI-based Similarity Algorithms
"""

import pytest
import numpy as np

# AI 의존성이 설치되지 않았을 수 있으므로 skip 처리
pytest.importorskip("torch")
pytest.importorskip("transformers")

from algorithms.ai_based.embedding_matcher import EmbeddingSimilarity
from algorithms.ai_based.hybrid import HybridSimilarity
from algorithms.traditional.mfcc import MFCCSimilarity


class TestEmbeddingSimilarity:
    """EmbeddingSimilarity 테스트"""

    @pytest.mark.slow
    def test_init(self):
        """초기화 테스트"""
        algo = EmbeddingSimilarity(
            model_name="wav2vec2-base",
            pooling="mean",
            distance_metric="cosine",
            device="cpu",
        )

        assert algo.model_name == "wav2vec2-base"
        assert algo.pooling == "mean"
        assert algo.distance_metric == "cosine"

    @pytest.mark.slow
    def test_compute_similarity(self, sample_audio_mono):
        """유사도 계산 테스트"""
        algo = EmbeddingSimilarity(device="cpu")
        audio_data, sample_rate = sample_audio_mono

        similarity = algo.compute_similarity(
            audio_data, audio_data, sample_rate, sample_rate
        )

        assert 0.0 <= similarity <= 1.0
        # 동일한 오디오이므로 유사도가 높아야 함
        assert similarity > 0.5

    @pytest.mark.slow
    def test_find_similar_segments(self, sample_audio_mono):
        """유사 세그먼트 찾기 테스트"""
        algo = EmbeddingSimilarity(
            device="cpu",
            window_size=0.5,
            hop_size=0.25,
        )
        audio_data, sample_rate = sample_audio_mono

        # 소스는 타겟을 2번 반복
        source_audio = np.tile(audio_data, 2)

        matches = algo.find_similar_segments(
            audio_data, source_audio, sample_rate, sample_rate, top_k=3
        )

        assert isinstance(matches, list)
        assert len(matches) <= 3

        # 유사도 정렬 확인
        for i in range(len(matches) - 1):
            assert matches[i].similarity >= matches[i + 1].similarity

    @pytest.mark.slow
    def test_different_distance_metrics(self, sample_audio_mono):
        """다양한 거리 메트릭 테스트"""
        audio_data, sample_rate = sample_audio_mono

        for metric in ["cosine", "euclidean"]:
            algo = EmbeddingSimilarity(
                distance_metric=metric,
                device="cpu",
            )

            similarity = algo.compute_similarity(
                audio_data, audio_data, sample_rate, sample_rate
            )

            assert 0.0 <= similarity <= 1.0

    @pytest.mark.slow
    def test_create_metadata(self):
        """메타데이터 생성 테스트"""
        algo = EmbeddingSimilarity(device="cpu")

        metadata = algo.create_metadata(
            inference_time=1.5,
            num_matches=5,
            similarities=[0.9, 0.8, 0.7, 0.6, 0.5],
        )

        assert metadata.model_name == "wav2vec2-base"
        assert metadata.inference_time == 1.5
        assert metadata.confidence_score > 0

    def test_repr(self):
        """문자열 표현 테스트"""
        algo = EmbeddingSimilarity(device="cpu")
        repr_str = repr(algo)

        assert "EmbeddingSimilarity" in repr_str
        assert "wav2vec2-base" in repr_str


class TestHybridSimilarity:
    """HybridSimilarity 테스트"""

    @pytest.mark.slow
    def test_init(self):
        """초기화 테스트"""
        trad_algo = MFCCSimilarity()
        ai_algo = EmbeddingSimilarity(device="cpu")

        hybrid = HybridSimilarity(
            traditional_algorithm=trad_algo,
            ai_algorithm=ai_algo,
            traditional_weight=0.4,
            ai_weight=0.6,
        )

        assert hybrid.traditional_weight == 0.4
        assert hybrid.ai_weight == 0.6

    @pytest.mark.slow
    def test_init_with_defaults(self):
        """기본값으로 초기화 테스트"""
        hybrid = HybridSimilarity()

        assert hybrid.traditional_algo is not None
        assert hybrid.ai_algo is not None

    @pytest.mark.slow
    def test_compute_similarity(self, sample_audio_mono):
        """하이브리드 유사도 계산 테스트"""
        hybrid = HybridSimilarity(
            traditional_weight=0.5,
            ai_weight=0.5,
        )
        audio_data, sample_rate = sample_audio_mono

        similarity = hybrid.compute_similarity(
            audio_data, audio_data, sample_rate, sample_rate
        )

        assert 0.0 <= similarity <= 1.0

    @pytest.mark.slow
    def test_find_similar_segments(self, sample_audio_mono):
        """하이브리드 세그먼트 찾기 테스트"""
        hybrid = HybridSimilarity()
        audio_data, sample_rate = sample_audio_mono

        source_audio = np.tile(audio_data, 2)

        matches = hybrid.find_similar_segments(
            audio_data, source_audio, sample_rate, sample_rate, top_k=3
        )

        assert isinstance(matches, list)

        # 하이브리드 메타데이터 확인
        if matches:
            assert matches[0].metadata.get("algorithm") == "hybrid"

    @pytest.mark.slow
    def test_different_fusion_methods(self, sample_audio_mono):
        """다양한 융합 방법 테스트"""
        audio_data, sample_rate = sample_audio_mono

        for method in ["weighted_average", "max", "min", "product"]:
            hybrid = HybridSimilarity(fusion_method=method)

            similarity = hybrid.compute_similarity(
                audio_data, audio_data, sample_rate, sample_rate
            )

            assert 0.0 <= similarity <= 1.0

    def test_repr(self):
        """문자열 표현 테스트"""
        hybrid = HybridSimilarity()
        repr_str = repr(hybrid)

        assert "HybridSimilarity" in repr_str
