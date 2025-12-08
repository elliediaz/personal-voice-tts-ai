"""
AI 모듈

AI 기반 오디오 분석 및 유사도 검출을 위한 핵심 모듈
transformers 패키지가 설치된 경우에만 사용 가능
"""

__all__ = []

try:
    from .model_manager import ModelManager
    from .metadata import AIMetadata
    __all__.extend(["ModelManager", "AIMetadata"])
    AI_AVAILABLE = True
except ImportError:
    ModelManager = None
    AIMetadata = None
    AI_AVAILABLE = False
