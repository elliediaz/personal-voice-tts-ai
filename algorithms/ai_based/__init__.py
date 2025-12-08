"""
AI 기반 유사도 알고리즘

딥러닝 모델을 활용한 오디오 유사도 검출 알고리즘
transformers 패키지가 설치된 경우에만 사용 가능
"""

__all__ = []

try:
    from .embeddings import EmbeddingExtractor
    from .embedding_matcher import EmbeddingSimilarity
    from .hybrid import HybridSimilarity
    __all__.extend([
        "EmbeddingExtractor",
        "EmbeddingSimilarity",
        "HybridSimilarity",
    ])
    AI_ALGORITHMS_AVAILABLE = True
except ImportError:
    EmbeddingExtractor = None
    EmbeddingSimilarity = None
    HybridSimilarity = None
    AI_ALGORITHMS_AVAILABLE = False
