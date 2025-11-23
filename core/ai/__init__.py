"""
AI 모듈

AI 기반 오디오 분석 및 유사도 검출을 위한 핵심 모듈
"""

from .model_manager import ModelManager
from .metadata import AIMetadata

__all__ = ["ModelManager", "AIMetadata"]
