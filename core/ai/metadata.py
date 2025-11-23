"""
AI Metadata

AI 분석 결과의 메타데이터를 관리하는 모듈
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List
import json
from pathlib import Path
from datetime import datetime


@dataclass
class AIMetadata:
    """AI 분석 메타데이터"""

    # 모델 정보
    model_name: str
    model_type: str  # 'wav2vec2', 'hubert', etc.

    # 추론 정보
    inference_time: float  # 추론 소요 시간 (초)
    device: str  # 'cuda' or 'cpu'
    embedding_dim: int  # 임베딩 차원

    # 신뢰도 정보
    confidence_score: float  # 전체 신뢰도
    similarity_scores: Optional[List[float]] = None  # 유사도 점수 목록

    # 주파수 분석
    frequency_analysis: Optional[Dict[str, Any]] = None

    # 추가 메타데이터
    metadata: Dict[str, Any] = field(default_factory=dict)

    # 타임스탬프
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """JSON 문자열로 변환"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def save(self, output_path: Path):
        """JSON 파일로 저장"""
        output_path = Path(output_path)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(self.to_json())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AIMetadata":
        """딕셔너리에서 로드"""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> "AIMetadata":
        """JSON 문자열에서 로드"""
        data = json.loads(json_str)
        return cls.from_dict(data)

    @classmethod
    def load(cls, input_path: Path) -> "AIMetadata":
        """JSON 파일에서 로드"""
        input_path = Path(input_path)
        with open(input_path, "r", encoding="utf-8") as f:
            json_str = f.read()
        return cls.from_json(json_str)

    def add_frequency_analysis(
        self,
        spectral_centroid: Optional[float] = None,
        spectral_rolloff: Optional[float] = None,
        spectral_bandwidth: Optional[float] = None,
        zero_crossing_rate: Optional[float] = None,
        **kwargs,
    ):
        """주파수 분석 정보 추가"""
        self.frequency_analysis = {
            "spectral_centroid": spectral_centroid,
            "spectral_rolloff": spectral_rolloff,
            "spectral_bandwidth": spectral_bandwidth,
            "zero_crossing_rate": zero_crossing_rate,
            **kwargs,
        }

    def add_metadata(self, key: str, value: Any):
        """추가 메타데이터 추가"""
        self.metadata[key] = value

    def get_summary(self) -> str:
        """요약 정보 반환"""
        lines = [
            "=" * 60,
            "AI 분석 메타데이터",
            "=" * 60,
            f"모델: {self.model_name} ({self.model_type})",
            f"디바이스: {self.device}",
            f"임베딩 차원: {self.embedding_dim}",
            f"추론 시간: {self.inference_time:.3f}초",
            f"신뢰도: {self.confidence_score:.3f}",
        ]

        if self.similarity_scores:
            avg_sim = sum(self.similarity_scores) / len(self.similarity_scores)
            lines.append(f"평균 유사도: {avg_sim:.3f}")
            lines.append(f"매치 개수: {len(self.similarity_scores)}")

        if self.frequency_analysis:
            lines.append("\n주파수 분석:")
            for key, value in self.frequency_analysis.items():
                if value is not None:
                    if isinstance(value, float):
                        lines.append(f"  {key}: {value:.2f}")
                    else:
                        lines.append(f"  {key}: {value}")

        if self.metadata:
            lines.append("\n추가 정보:")
            for key, value in self.metadata.items():
                lines.append(f"  {key}: {value}")

        lines.append(f"\n분석 시간: {self.timestamp}")
        lines.append("=" * 60)

        return "\n".join(lines)

    def __repr__(self) -> str:
        return (
            f"AIMetadata(model={self.model_name}, "
            f"confidence={self.confidence_score:.3f}, "
            f"device={self.device})"
        )
