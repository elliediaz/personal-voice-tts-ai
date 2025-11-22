"""
TTS Backends

다양한 TTS 엔진 백엔드 구현
"""

from .gtts_backend import GTTSBackend
from .pyttsx3_backend import Pyttsx3Backend
from .edge_backend import EdgeTTSBackend

__all__ = [
    "GTTSBackend",
    "Pyttsx3Backend",
    "EdgeTTSBackend",
]
