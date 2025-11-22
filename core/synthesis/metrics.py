"""
Quality Metrics

오디오 품질 메트릭 측정 모듈
"""

import logging
from typing import Dict, Any

import numpy as np
import librosa

logger = logging.getLogger(__name__)


class QualityMetrics:
    """품질 메트릭 클래스"""

    def __init__(self):
        """초기화"""
        logger.info("QualityMetrics 초기화")

    def compute_snr(
        self, clean: np.ndarray, noisy: np.ndarray
    ) -> float:
        """
        SNR (Signal-to-Noise Ratio) 계산

        Args:
            clean: 깨끗한 신호
            noisy: 노이즈가 있는 신호

        Returns:
            SNR (dB)
        """
        # 길이 맞추기
        min_len = min(len(clean), len(noisy))
        clean = clean[:min_len]
        noisy = noisy[:min_len]

        # 노이즈 = 노이즈 신호 - 깨끗한 신호
        noise = noisy - clean

        # 파워 계산
        signal_power = np.mean(clean**2)
        noise_power = np.mean(noise**2)

        # SNR (dB)
        if noise_power > 0:
            snr = 10 * np.log10(signal_power / noise_power)
        else:
            snr = float("inf")

        return float(snr)

    def compute_mse(
        self, reference: np.ndarray, degraded: np.ndarray
    ) -> float:
        """
        MSE (Mean Squared Error) 계산

        Args:
            reference: 참조 신호
            degraded: 품질 저하 신호

        Returns:
            MSE
        """
        min_len = min(len(reference), len(degraded))
        reference = reference[:min_len]
        degraded = degraded[:min_len]

        mse = np.mean((reference - degraded) ** 2)

        return float(mse)

    def compute_spectral_distance(
        self,
        audio1: np.ndarray,
        audio2: np.ndarray,
        sample_rate: int,
    ) -> float:
        """
        스펙트럼 거리 계산

        Args:
            audio1: 첫 번째 오디오
            audio2: 두 번째 오디오
            sample_rate: 샘플링 레이트

        Returns:
            스펙트럼 거리
        """
        # 길이 맞추기
        min_len = min(len(audio1), len(audio2))
        audio1 = audio1[:min_len]
        audio2 = audio2[:min_len]

        # Mel 스펙트로그램
        mel1 = librosa.feature.melspectrogram(y=audio1, sr=sample_rate)
        mel2 = librosa.feature.melspectrogram(y=audio2, sr=sample_rate)

        # dB 스케일
        mel1_db = librosa.power_to_db(mel1)
        mel2_db = librosa.power_to_db(mel2)

        # 유클리드 거리
        distance = np.sqrt(np.mean((mel1_db - mel2_db) ** 2))

        return float(distance)

    def compute_zero_crossing_rate(
        self, audio: np.ndarray
    ) -> float:
        """
        Zero Crossing Rate 계산

        Args:
            audio: 오디오 데이터

        Returns:
            ZCR (비율)
        """
        zcr = librosa.feature.zero_crossing_rate(audio)[0]
        return float(np.mean(zcr))

    def compute_rms_energy(
        self, audio: np.ndarray
    ) -> float:
        """
        RMS 에너지 계산

        Args:
            audio: 오디오 데이터

        Returns:
            RMS 에너지
        """
        rms = librosa.feature.rms(y=audio)[0]
        return float(np.mean(rms))

    def compute_spectral_centroid(
        self, audio: np.ndarray, sample_rate: int
    ) -> float:
        """
        스펙트럼 중심 계산

        Args:
            audio: 오디오 데이터
            sample_rate: 샘플링 레이트

        Returns:
            스펙트럼 중심 (Hz)
        """
        centroid = librosa.feature.spectral_centroid(y=audio, sr=sample_rate)[0]
        return float(np.mean(centroid))

    def detect_clipping(
        self, audio: np.ndarray, threshold: float = 0.99
    ) -> dict:
        """
        클리핑 검출

        Args:
            audio: 오디오 데이터
            threshold: 클리핑 임계값

        Returns:
            클리핑 정보 딕셔너리
        """
        clipped_samples = np.sum(np.abs(audio) >= threshold)
        clipping_ratio = clipped_samples / len(audio)

        return {
            "clipped_samples": int(clipped_samples),
            "total_samples": len(audio),
            "clipping_ratio": float(clipping_ratio),
            "is_clipped": clipping_ratio > 0.001,  # 0.1% 이상이면 클리핑
        }

    def detect_silence(
        self, audio: np.ndarray, sample_rate: int, threshold_db: float = -40
    ) -> dict:
        """
        무음 구간 검출

        Args:
            audio: 오디오 데이터
            sample_rate: 샘플링 레이트
            threshold_db: 무음 임계값 (dB)

        Returns:
            무음 정보 딕셔너리
        """
        # 무음 구간 인덱스
        intervals = librosa.effects.split(
            audio, top_db=-threshold_db
        )

        # 무음 구간 길이 계산
        if len(intervals) > 0:
            non_silent_samples = np.sum([end - start for start, end in intervals])
            silent_samples = len(audio) - non_silent_samples
        else:
            silent_samples = len(audio)
            non_silent_samples = 0

        silence_ratio = silent_samples / len(audio)

        return {
            "silent_samples": int(silent_samples),
            "non_silent_samples": int(non_silent_samples),
            "silence_ratio": float(silence_ratio),
            "num_silent_intervals": len(intervals),
        }

    def analyze_quality(
        self,
        audio: np.ndarray,
        sample_rate: int,
        reference: Optional[np.ndarray] = None,
    ) -> Dict[str, Any]:
        """
        종합 품질 분석

        Args:
            audio: 분석할 오디오
            sample_rate: 샘플링 레이트
            reference: 참조 오디오 (옵션)

        Returns:
            품질 분석 결과 딕셔너리
        """
        results = {}

        # 기본 메트릭
        results["rms_energy"] = self.compute_rms_energy(audio)
        results["zero_crossing_rate"] = self.compute_zero_crossing_rate(audio)
        results["spectral_centroid"] = self.compute_spectral_centroid(audio, sample_rate)

        # 클리핑 검출
        results["clipping"] = self.detect_clipping(audio)

        # 무음 검출
        results["silence"] = self.detect_silence(audio, sample_rate)

        # 참조 오디오가 있으면 비교 메트릭 계산
        if reference is not None:
            results["snr"] = self.compute_snr(reference, audio)
            results["mse"] = self.compute_mse(reference, audio)
            results["spectral_distance"] = self.compute_spectral_distance(
                reference, audio, sample_rate
            )

        return results

    def get_quality_score(
        self,
        analysis_results: Dict[str, Any],
    ) -> float:
        """
        품질 점수 계산 (0~1, 높을수록 좋음)

        Args:
            analysis_results: analyze_quality() 결과

        Returns:
            품질 점수
        """
        score = 1.0

        # 클리핑 페널티
        if analysis_results["clipping"]["is_clipped"]:
            score -= 0.3 * analysis_results["clipping"]["clipping_ratio"]

        # 무음 페널티
        if analysis_results["silence"]["silence_ratio"] > 0.5:
            score -= 0.2

        # RMS 에너지 점수 (너무 낮으면 감점)
        if analysis_results["rms_energy"] < 0.01:
            score -= 0.2

        # 점수 범위 제한
        score = max(0.0, min(1.0, score))

        return score

    def __repr__(self) -> str:
        return "QualityMetrics()"
