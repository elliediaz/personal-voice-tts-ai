"""
Embedding Extractor

오디오에서 딥러닝 임베딩을 추출하는 모듈
"""

import logging
from typing import Optional, Union, Literal
import time

import numpy as np
import torch
import librosa

from core.ai.model_manager import ModelManager

logger = logging.getLogger(__name__)


class EmbeddingExtractor:
    """오디오 임베딩 추출 클래스"""

    def __init__(
        self,
        model_name: str = "wav2vec2-base",
        pooling: Literal["mean", "max", "attention"] = "mean",
        normalize: bool = True,
        batch_size: int = 8,
        device: Optional[str] = None,
    ):
        """
        Args:
            model_name: 사용할 모델 이름
            pooling: 임베딩 풀링 방법 ('mean', 'max', 'attention')
            normalize: 임베딩 정규화 여부
            batch_size: 배치 크기
            device: 디바이스 ('cuda', 'cpu', None=auto)
        """
        self.model_name = model_name
        self.pooling = pooling
        self.normalize = normalize
        self.batch_size = batch_size

        # 모델 매니저 초기화
        self.model_manager = ModelManager(device=device)
        self.device = self.model_manager.get_device()

        # 모델 로드
        self.model, self.processor = self.model_manager.load_model(model_name)

        logger.info(
            f"EmbeddingExtractor 초기화: {model_name} (pooling={pooling}, device={self.device})"
        )

    def extract(
        self,
        audio: np.ndarray,
        sample_rate: int,
        return_time: bool = False,
    ) -> Union[np.ndarray, tuple]:
        """
        오디오에서 임베딩 추출

        Args:
            audio: 오디오 데이터 (numpy array)
            sample_rate: 샘플링 레이트
            return_time: 추론 시간 반환 여부

        Returns:
            임베딩 벡터 (numpy array) 또는 (임베딩, 추론시간) 튜플
        """
        start_time = time.time()

        # 모노 변환
        if audio.ndim > 1:
            audio = librosa.to_mono(audio)

        # 리샘플링 (모델은 16kHz 필요)
        target_sr = 16000
        if sample_rate != target_sr:
            audio = librosa.resample(audio, orig_sr=sample_rate, target_sr=target_sr)

        # 전처리
        inputs = self.processor(
            audio,
            sampling_rate=target_sr,
            return_tensors="pt",
        )

        # 디바이스로 이동
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # 추론
        with torch.no_grad():
            outputs = self.model(**inputs)
            hidden_states = outputs.last_hidden_state  # (batch, time, dim)

        # 풀링
        embedding = self._pool_embeddings(hidden_states)

        # 정규화
        if self.normalize:
            embedding = torch.nn.functional.normalize(embedding, p=2, dim=-1)

        # numpy로 변환
        embedding_np = embedding.cpu().numpy().squeeze()

        inference_time = time.time() - start_time

        if return_time:
            return embedding_np, inference_time
        return embedding_np

    def extract_batch(
        self,
        audios: list,
        sample_rates: list,
        show_progress: bool = True,
    ) -> np.ndarray:
        """
        여러 오디오에서 임베딩 추출 (배치 처리)

        Args:
            audios: 오디오 리스트
            sample_rates: 샘플링 레이트 리스트
            show_progress: 진행률 표시 여부

        Returns:
            임베딩 행렬 (num_audios, embedding_dim)
        """
        if len(audios) != len(sample_rates):
            raise ValueError("오디오 개수와 샘플링 레이트 개수가 일치하지 않습니다")

        embeddings = []

        if show_progress:
            try:
                from tqdm import tqdm

                iterator = tqdm(range(len(audios)), desc="임베딩 추출")
            except ImportError:
                iterator = range(len(audios))
        else:
            iterator = range(len(audios))

        for i in iterator:
            embedding = self.extract(audios[i], sample_rates[i])
            embeddings.append(embedding)

        return np.array(embeddings)

    def _pool_embeddings(self, hidden_states: torch.Tensor) -> torch.Tensor:
        """
        임베딩 풀링

        Args:
            hidden_states: (batch, time, dim)

        Returns:
            pooled: (batch, dim)
        """
        if self.pooling == "mean":
            return hidden_states.mean(dim=1)
        elif self.pooling == "max":
            return hidden_states.max(dim=1)[0]
        elif self.pooling == "attention":
            return self._attention_pooling(hidden_states)
        else:
            raise ValueError(f"지원하지 않는 풀링 방법: {self.pooling}")

    def _attention_pooling(self, hidden_states: torch.Tensor) -> torch.Tensor:
        """
        어텐션 기반 풀링

        Args:
            hidden_states: (batch, time, dim)

        Returns:
            pooled: (batch, dim)
        """
        # 간단한 self-attention 풀링
        # Q = K = V = hidden_states
        batch_size, seq_len, hidden_dim = hidden_states.shape

        # Attention weights: (batch, time, time)
        attention_scores = torch.matmul(
            hidden_states, hidden_states.transpose(-1, -2)
        ) / (hidden_dim**0.5)

        attention_weights = torch.nn.functional.softmax(attention_scores, dim=-1)

        # Weighted sum: (batch, time, dim)
        attended = torch.matmul(attention_weights, hidden_states)

        # Mean over time: (batch, dim)
        pooled = attended.mean(dim=1)

        return pooled

    def get_embedding_dim(self) -> int:
        """임베딩 차원 반환"""
        # 더미 오디오로 차원 확인
        dummy_audio = np.random.randn(16000).astype(np.float32)
        embedding = self.extract(dummy_audio, 16000)
        return embedding.shape[0]

    def __repr__(self) -> str:
        return (
            f"EmbeddingExtractor(model={self.model_name}, "
            f"pooling={self.pooling}, device={self.device})"
        )
