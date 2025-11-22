"""
Tests for AI Metadata
"""

import pytest
import tempfile
from pathlib import Path

from core.ai.metadata import AIMetadata


class TestAIMetadata:
    """AIMetadata 테스트"""

    def test_init(self):
        """초기화 테스트"""
        metadata = AIMetadata(
            model_name="wav2vec2-base",
            model_type="wav2vec2",
            inference_time=1.5,
            device="cpu",
            embedding_dim=768,
            confidence_score=0.85,
        )

        assert metadata.model_name == "wav2vec2-base"
        assert metadata.model_type == "wav2vec2"
        assert metadata.inference_time == 1.5
        assert metadata.device == "cpu"
        assert metadata.embedding_dim == 768
        assert metadata.confidence_score == 0.85

    def test_to_dict(self):
        """딕셔너리 변환 테스트"""
        metadata = AIMetadata(
            model_name="wav2vec2-base",
            model_type="wav2vec2",
            inference_time=1.5,
            device="cpu",
            embedding_dim=768,
            confidence_score=0.85,
        )

        data = metadata.to_dict()

        assert isinstance(data, dict)
        assert data["model_name"] == "wav2vec2-base"
        assert data["inference_time"] == 1.5

    def test_to_json(self):
        """JSON 변환 테스트"""
        metadata = AIMetadata(
            model_name="wav2vec2-base",
            model_type="wav2vec2",
            inference_time=1.5,
            device="cpu",
            embedding_dim=768,
            confidence_score=0.85,
        )

        json_str = metadata.to_json()

        assert isinstance(json_str, str)
        assert "wav2vec2-base" in json_str
        assert "1.5" in json_str

    def test_save_load(self):
        """저장 및 로드 테스트"""
        metadata = AIMetadata(
            model_name="wav2vec2-base",
            model_type="wav2vec2",
            inference_time=1.5,
            device="cpu",
            embedding_dim=768,
            confidence_score=0.85,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "metadata.json"

            # 저장
            metadata.save(output_path)
            assert output_path.exists()

            # 로드
            loaded = AIMetadata.load(output_path)

            assert loaded.model_name == metadata.model_name
            assert loaded.inference_time == metadata.inference_time
            assert loaded.embedding_dim == metadata.embedding_dim

    def test_add_frequency_analysis(self):
        """주파수 분석 추가 테스트"""
        metadata = AIMetadata(
            model_name="wav2vec2-base",
            model_type="wav2vec2",
            inference_time=1.5,
            device="cpu",
            embedding_dim=768,
            confidence_score=0.85,
        )

        metadata.add_frequency_analysis(
            spectral_centroid=1500.0,
            spectral_rolloff=3000.0,
        )

        assert metadata.frequency_analysis is not None
        assert metadata.frequency_analysis["spectral_centroid"] == 1500.0
        assert metadata.frequency_analysis["spectral_rolloff"] == 3000.0

    def test_add_metadata(self):
        """추가 메타데이터 테스트"""
        metadata = AIMetadata(
            model_name="wav2vec2-base",
            model_type="wav2vec2",
            inference_time=1.5,
            device="cpu",
            embedding_dim=768,
            confidence_score=0.85,
        )

        metadata.add_metadata("custom_key", "custom_value")

        assert metadata.metadata["custom_key"] == "custom_value"

    def test_get_summary(self):
        """요약 정보 테스트"""
        metadata = AIMetadata(
            model_name="wav2vec2-base",
            model_type="wav2vec2",
            inference_time=1.5,
            device="cpu",
            embedding_dim=768,
            confidence_score=0.85,
            similarity_scores=[0.9, 0.8, 0.7],
        )

        summary = metadata.get_summary()

        assert isinstance(summary, str)
        assert "wav2vec2-base" in summary
        assert "1.5" in summary
        assert "0.85" in summary

    def test_repr(self):
        """문자열 표현 테스트"""
        metadata = AIMetadata(
            model_name="wav2vec2-base",
            model_type="wav2vec2",
            inference_time=1.5,
            device="cpu",
            embedding_dim=768,
            confidence_score=0.85,
        )

        repr_str = repr(metadata)

        assert "AIMetadata" in repr_str
        assert "wav2vec2-base" in repr_str
        assert "0.85" in repr_str
