"""
AI 기반 유사도 알고리즘

딥러닝 모델을 활용한 오디오 유사도 검출 알고리즘
"""

from .embeddings import EmbeddingExtractor
from .embedding_matcher import EmbeddingSimilarity
from .hybrid import HybridSimilarity

__all__ = [
    "EmbeddingExtractor",
    "EmbeddingSimilarity",
    "HybridSimilarity",
]
