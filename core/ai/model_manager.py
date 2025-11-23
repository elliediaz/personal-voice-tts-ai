"""
Model Manager

AI 모델 다운로드, 캐싱, 관리를 담당하는 모듈
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any, Union
import logging

import torch
from transformers import (
    Wav2Vec2Model,
    Wav2Vec2Processor,
    HubertModel,
    AutoFeatureExtractor,
)

logger = logging.getLogger(__name__)


class ModelManager:
    """AI 모델 관리 클래스"""

    # 지원하는 모델 목록
    SUPPORTED_MODELS = {
        "wav2vec2-base": "facebook/wav2vec2-base",
        "wav2vec2-large": "facebook/wav2vec2-large-960h",
        "hubert-base": "facebook/hubert-base-ls960",
        "hubert-large": "facebook/hubert-large-ll60k",
    }

    def __init__(
        self,
        cache_dir: Optional[Union[str, Path]] = None,
        device: Optional[str] = None,
    ):
        """
        Args:
            cache_dir: 모델 캐시 디렉토리 (기본: ~/.cache/personal-voice-tts-ai)
            device: 사용할 디바이스 ('cuda', 'cpu', None=auto)
        """
        self.cache_dir = Path(cache_dir) if cache_dir else self._get_default_cache_dir()
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 디바이스 설정
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        logger.info(f"ModelManager 초기화 완료 (device: {self.device})")

        # 로드된 모델 캐시
        self._loaded_models: Dict[str, Any] = {}
        self._loaded_processors: Dict[str, Any] = {}

    @staticmethod
    def _get_default_cache_dir() -> Path:
        """기본 캐시 디렉토리 반환"""
        return Path.home() / ".cache" / "personal-voice-tts-ai" / "models"

    def list_available_models(self) -> list:
        """사용 가능한 모델 목록 반환"""
        return list(self.SUPPORTED_MODELS.keys())

    def get_model_info(self, model_name: str) -> Dict[str, str]:
        """모델 정보 반환"""
        if model_name not in self.SUPPORTED_MODELS:
            raise ValueError(f"지원하지 않는 모델: {model_name}")

        return {
            "name": model_name,
            "huggingface_id": self.SUPPORTED_MODELS[model_name],
            "type": "wav2vec2" if "wav2vec2" in model_name else "hubert",
        }

    def load_model(
        self,
        model_name: str,
        force_download: bool = False,
    ) -> tuple:
        """
        모델과 프로세서를 로드합니다.

        Args:
            model_name: 모델 이름 (예: 'wav2vec2-base')
            force_download: 강제로 재다운로드 여부

        Returns:
            (model, processor) 튜플
        """
        if model_name not in self.SUPPORTED_MODELS:
            raise ValueError(
                f"지원하지 않는 모델: {model_name}. "
                f"사용 가능한 모델: {', '.join(self.SUPPORTED_MODELS.keys())}"
            )

        # 이미 로드된 모델이 있으면 반환
        if not force_download and model_name in self._loaded_models:
            logger.info(f"캐시된 모델 사용: {model_name}")
            return self._loaded_models[model_name], self._loaded_processors[model_name]

        logger.info(f"모델 로드 중: {model_name}")

        model_id = self.SUPPORTED_MODELS[model_name]
        model_type = "wav2vec2" if "wav2vec2" in model_name else "hubert"

        try:
            # 모델과 프로세서 로드
            if model_type == "wav2vec2":
                model = Wav2Vec2Model.from_pretrained(
                    model_id,
                    cache_dir=self.cache_dir,
                )
                processor = Wav2Vec2Processor.from_pretrained(
                    model_id,
                    cache_dir=self.cache_dir,
                )
            else:  # hubert
                model = HubertModel.from_pretrained(
                    model_id,
                    cache_dir=self.cache_dir,
                )
                processor = AutoFeatureExtractor.from_pretrained(
                    model_id,
                    cache_dir=self.cache_dir,
                )

            # 디바이스로 이동
            model = model.to(self.device)
            model.eval()  # 평가 모드

            # 캐시에 저장
            self._loaded_models[model_name] = model
            self._loaded_processors[model_name] = processor

            logger.info(f"모델 로드 완료: {model_name} (device: {self.device})")

            return model, processor

        except Exception as e:
            logger.error(f"모델 로드 실패: {model_name} - {str(e)}")
            raise

    def unload_model(self, model_name: str):
        """모델을 메모리에서 해제"""
        if model_name in self._loaded_models:
            del self._loaded_models[model_name]
            del self._loaded_processors[model_name]

            # GPU 메모리 정리
            if self.device == "cuda":
                torch.cuda.empty_cache()

            logger.info(f"모델 해제 완료: {model_name}")

    def unload_all_models(self):
        """모든 모델을 메모리에서 해제"""
        model_names = list(self._loaded_models.keys())
        for model_name in model_names:
            self.unload_model(model_name)

    def warm_up(self, model_name: str, sample_length: int = 16000):
        """
        모델 웜업 (첫 추론 최적화)

        Args:
            model_name: 모델 이름
            sample_length: 샘플 오디오 길이
        """
        logger.info(f"모델 웜업 중: {model_name}")

        model, processor = self.load_model(model_name)

        # 더미 입력 생성
        dummy_audio = torch.randn(sample_length)

        with torch.no_grad():
            inputs = processor(
                dummy_audio,
                sampling_rate=16000,
                return_tensors="pt",
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            _ = model(**inputs)

        logger.info(f"모델 웜업 완료: {model_name}")

    def get_device(self) -> str:
        """현재 디바이스 반환"""
        return self.device

    def get_model_size(self, model_name: str) -> Optional[int]:
        """
        모델 크기 반환 (바이트)

        Args:
            model_name: 모델 이름

        Returns:
            모델 크기 (바이트), 로드되지 않은 경우 None
        """
        if model_name not in self._loaded_models:
            return None

        model = self._loaded_models[model_name]
        return sum(p.numel() * p.element_size() for p in model.parameters())

    def get_cache_dir(self) -> Path:
        """캐시 디렉토리 반환"""
        return self.cache_dir

    def clear_cache(self):
        """캐시 디렉토리 삭제 (모든 다운로드된 모델 제거)"""
        import shutil

        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info("모델 캐시 삭제 완료")

    def __repr__(self) -> str:
        loaded = len(self._loaded_models)
        total = len(self.SUPPORTED_MODELS)
        return f"ModelManager(device={self.device}, loaded={loaded}/{total})"
