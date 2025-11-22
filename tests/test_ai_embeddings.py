"""
Tests for AI Embedding Extractor
"""

import pytest
import numpy as np

# AI 의존성이 설치되지 않았을 수 있으므로 skip 처리
pytest.importorskip("torch")
pytest.importorskip("transformers")

from algorithms.ai_based.embeddings import EmbeddingExtractor


class TestEmbeddingExtractor:
    """EmbeddingExtractor 테스트"""

    @pytest.fixture
    def extractor(self):
        """기본 추출기 fixture"""
        return EmbeddingExtractor(
            model_name="wav2vec2-base",
            pooling="mean",
            device="cpu",
        )

    @pytest.mark.slow
    def test_init(self):
        """초기화 테스트 (느림 - 모델 로드)"""
        extractor = EmbeddingExtractor(device="cpu")

        assert extractor.model_name == "wav2vec2-base"
        assert extractor.pooling == "mean"
        assert extractor.device == "cpu"

    @pytest.mark.slow
    def test_extract(self, extractor, sample_audio_mono):
        """임베딩 추출 테스트"""
        audio_data, sample_rate = sample_audio_mono

        embedding = extractor.extract(audio_data, sample_rate)

        assert isinstance(embedding, np.ndarray)
        assert embedding.ndim == 1
        assert len(embedding) > 0

    @pytest.mark.slow
    def test_extract_with_time(self, extractor, sample_audio_mono):
        """추론 시간 포함 추출 테스트"""
        audio_data, sample_rate = sample_audio_mono

        embedding, inference_time = extractor.extract(
            audio_data, sample_rate, return_time=True
        )

        assert isinstance(embedding, np.ndarray)
        assert isinstance(inference_time, float)
        assert inference_time > 0

    @pytest.mark.slow
    def test_extract_batch(self, extractor, sample_audio_mono):
        """배치 추출 테스트"""
        audio_data, sample_rate = sample_audio_mono

        # 3개의 오디오 생성
        audios = [audio_data, audio_data, audio_data]
        sample_rates = [sample_rate, sample_rate, sample_rate]

        embeddings = extractor.extract_batch(
            audios, sample_rates, show_progress=False
        )

        assert embeddings.shape[0] == 3
        assert embeddings.ndim == 2

    @pytest.mark.slow
    def test_different_pooling(self, sample_audio_mono):
        """다양한 풀링 방법 테스트"""
        audio_data, sample_rate = sample_audio_mono

        for pooling in ["mean", "max"]:
            extractor = EmbeddingExtractor(
                model_name="wav2vec2-base",
                pooling=pooling,
                device="cpu",
            )

            embedding = extractor.extract(audio_data, sample_rate)

            assert isinstance(embedding, np.ndarray)
            assert len(embedding) > 0

    def test_repr(self, extractor):
        """문자열 표현 테스트"""
        repr_str = repr(extractor)

        assert "EmbeddingExtractor" in repr_str
        assert "wav2vec2-base" in repr_str
        assert "mean" in repr_str
