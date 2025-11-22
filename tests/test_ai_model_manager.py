"""
Tests for AI Model Manager
"""

import pytest
import tempfile
from pathlib import Path

# AI 의존성이 설치되지 않았을 수 있으므로 skip 처리
pytest.importorskip("torch")
pytest.importorskip("transformers")

from core.ai.model_manager import ModelManager


class TestModelManager:
    """ModelManager 테스트"""

    def test_init(self):
        """초기화 테스트"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ModelManager(cache_dir=tmpdir, device="cpu")

            assert manager.cache_dir == Path(tmpdir)
            assert manager.device == "cpu"
            assert len(manager._loaded_models) == 0

    def test_list_available_models(self):
        """사용 가능한 모델 목록 테스트"""
        manager = ModelManager(device="cpu")
        models = manager.list_available_models()

        assert isinstance(models, list)
        assert len(models) > 0
        assert "wav2vec2-base" in models
        assert "hubert-base" in models

    def test_get_model_info(self):
        """모델 정보 가져오기 테스트"""
        manager = ModelManager(device="cpu")

        info = manager.get_model_info("wav2vec2-base")

        assert info["name"] == "wav2vec2-base"
        assert "huggingface_id" in info
        assert info["type"] == "wav2vec2"

    def test_get_model_info_invalid(self):
        """잘못된 모델 정보 테스트"""
        manager = ModelManager(device="cpu")

        with pytest.raises(ValueError, match="지원하지 않는 모델"):
            manager.get_model_info("invalid_model")

    @pytest.mark.slow
    def test_load_model(self):
        """모델 로드 테스트 (느림 - 실제 다운로드)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ModelManager(cache_dir=tmpdir, device="cpu")

            model, processor = manager.load_model("wav2vec2-base")

            assert model is not None
            assert processor is not None
            assert "wav2vec2-base" in manager._loaded_models

    def test_get_device(self):
        """디바이스 가져오기 테스트"""
        manager = ModelManager(device="cpu")

        assert manager.get_device() == "cpu"

    def test_repr(self):
        """문자열 표현 테스트"""
        manager = ModelManager(device="cpu")
        repr_str = repr(manager)

        assert "ModelManager" in repr_str
        assert "cpu" in repr_str
