"""
Rhythm Similarity Algorithm

리듬 특징을 사용한 유사도 검출 알고리즘입니다.
"""

from typing import List
import numpy as np
import librosa
from tqdm import tqdm

from algorithms.base import BaseSimilarityAlgorithm, SimilarityMatch
from utils.logging import get_logger

logger = get_logger(__name__)


class RhythmSimilarity(BaseSimilarityAlgorithm):
    """
    리듬 기반 유사도 알고리즘.

    템포, 비트, 온셋 등의 리듬 특징을 비교하여 유사도를 계산합니다.
    """

    def __init__(
        self,
        hop_length: int = 512,
        use_tempo: bool = True,
        use_onset: bool = True,
        **kwargs
    ):
        """
        RhythmSimilarity를 초기화합니다.

        Args:
            hop_length: 홉 길이
            use_tempo: 템포 특징 사용 여부
            use_onset: 온셋 특징 사용 여부
            **kwargs: 기본 클래스 파라미터
        """
        super().__init__(**kwargs)

        self.hop_length = hop_length
        self.use_tempo = use_tempo
        self.use_onset = use_onset

        logger.info(f"RhythmSimilarity 초기화 완료")

    def _extract_rhythm_features(
        self,
        audio: np.ndarray,
        sr: int,
    ) -> dict:
        """
        리듬 특징을 추출합니다.

        Args:
            audio: 오디오 데이터
            sr: 샘플링 레이트

        Returns:
            dict: 리듬 특징 딕셔너리
        """
        features = {}

        if self.use_tempo:
            # 템포 추정
            tempo, beats = librosa.beat.beat_track(
                y=audio,
                sr=sr,
                hop_length=self.hop_length,
            )
            features['tempo'] = tempo
            features['beats'] = beats

        if self.use_onset:
            # 온셋 강도
            onset_env = librosa.onset.onset_strength(
                y=audio,
                sr=sr,
                hop_length=self.hop_length,
            )
            features['onset_env'] = onset_env

        return features

    def compute_similarity(
        self,
        target_audio: np.ndarray,
        source_audio: np.ndarray,
        target_sr: int,
        source_sr: int,
    ) -> float:
        """
        두 오디오 간의 리듬 기반 유사도를 계산합니다.
        """
        self._validate_audio(target_audio, target_sr, "target_audio")
        self._validate_audio(source_audio, source_sr, "source_audio")

        target_features = self._extract_rhythm_features(target_audio, target_sr)
        source_features = self._extract_rhythm_features(source_audio, source_sr)

        similarities = []

        # 템포 유사도
        if self.use_tempo and 'tempo' in target_features:
            tempo_diff = abs(target_features['tempo'] - source_features['tempo'])
            # 템포 차이를 유사도로 변환 (최대 60 BPM 차이 허용)
            tempo_sim = max(0.0, 1.0 - tempo_diff / 60.0)
            similarities.append(tempo_sim)

        # 온셋 엔벨로프 유사도
        if self.use_onset and 'onset_env' in target_features:
            min_len = min(len(target_features['onset_env']), len(source_features['onset_env']))
            target_onset = target_features['onset_env'][:min_len]
            source_onset = source_features['onset_env'][:min_len]

            # 정규화
            target_onset = (target_onset - np.mean(target_onset)) / (np.std(target_onset) + 1e-8)
            source_onset = (source_onset - np.mean(source_onset)) / (np.std(source_onset) + 1e-8)

            # 상관 계수
            correlation = np.corrcoef(target_onset, source_onset)[0, 1]
            onset_sim = abs(correlation)
            similarities.append(onset_sim)

        # 평균 유사도
        if similarities:
            return np.mean(similarities)
        else:
            return 0.0

    def find_similar_segments(
        self,
        target_audio: np.ndarray,
        source_audio: np.ndarray,
        target_sr: int,
        source_sr: int,
        top_k: int = 10,
    ) -> List[SimilarityMatch]:
        """
        타겟 오디오와 유사한 소스 오디오의 세그먼트를 찾습니다.
        """
        self._validate_audio(target_audio, target_sr, "target_audio")
        self._validate_audio(source_audio, source_sr, "source_audio")

        target_duration = len(target_audio) / target_sr
        window_duration = min(target_duration, self.segment_max_length)
        window_samples = int(window_duration * source_sr)
        step_samples = window_samples // 2

        matches = []
        num_windows = (len(source_audio) - window_samples) // step_samples + 1

        target_features = self._extract_rhythm_features(target_audio, target_sr)

        for i in tqdm(range(num_windows), desc="Searching segments", disable=num_windows < 10):
            start_sample = i * step_samples
            end_sample = start_sample + window_samples

            if end_sample > len(source_audio):
                break

            window_audio = source_audio[start_sample:end_sample]
            window_features = self._extract_rhythm_features(window_audio, source_sr)

            similarities = []

            # 템포 유사도
            if self.use_tempo and 'tempo' in target_features:
                tempo_diff = abs(target_features['tempo'] - window_features['tempo'])
                tempo_sim = max(0.0, 1.0 - tempo_diff / 60.0)
                similarities.append(tempo_sim)

            # 온셋 엔벨로프 유사도
            if self.use_onset and 'onset_env' in target_features:
                min_len = min(len(target_features['onset_env']), len(window_features['onset_env']))
                target_onset = target_features['onset_env'][:min_len]
                window_onset = window_features['onset_env'][:min_len]

                target_onset = (target_onset - np.mean(target_onset)) / (np.std(target_onset) + 1e-8)
                window_onset = (window_onset - np.mean(window_onset)) / (np.std(window_onset) + 1e-8)

                correlation = np.corrcoef(target_onset, window_onset)[0, 1]
                onset_sim = abs(correlation)
                similarities.append(onset_sim)

            similarity = np.mean(similarities) if similarities else 0.0

            if similarity >= self.similarity_threshold:
                match = SimilarityMatch(
                    target_start=0.0,
                    target_end=target_duration,
                    source_start=start_sample / source_sr,
                    source_end=end_sample / source_sr,
                    similarity=similarity,
                    confidence=1.0,
                    metadata={
                        'target_tempo': target_features.get('tempo'),
                        'source_tempo': window_features.get('tempo'),
                    }
                )
                matches.append(match)

        return self._filter_matches(matches, top_k)


__all__ = ["RhythmSimilarity"]
