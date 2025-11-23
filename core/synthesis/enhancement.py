"""
Quality Enhancement

오디오 품질 향상 모듈
"""

import logging
from typing import Optional

import numpy as np
import librosa
from scipy import signal

logger = logging.getLogger(__name__)


class QualityEnhancer:
    """품질 향상 클래스"""

    def __init__(
        self,
        noise_reduction: bool = True,
        spectral_smoothing: bool = True,
        dynamic_range_compression: bool = False,
        equalization: bool = False,
    ):
        """
        Args:
            noise_reduction: 노이즈 감소 여부
            spectral_smoothing: 스펙트럼 스무딩 여부
            dynamic_range_compression: 다이나믹 레인지 압축 여부
            equalization: 이퀄라이제이션 여부
        """
        self.noise_reduction = noise_reduction
        self.spectral_smoothing = spectral_smoothing
        self.dynamic_range_compression = dynamic_range_compression
        self.equalization = equalization

        logger.info(
            f"QualityEnhancer 초기화: noise_reduction={noise_reduction}, "
            f"spectral_smoothing={spectral_smoothing}"
        )

    def enhance(
        self,
        audio: np.ndarray,
        sample_rate: int,
    ) -> np.ndarray:
        """
        오디오 품질 향상

        Args:
            audio: 오디오 데이터
            sample_rate: 샘플링 레이트

        Returns:
            향상된 오디오
        """
        enhanced = audio.copy()

        # 1. 노이즈 감소
        if self.noise_reduction:
            enhanced = self._reduce_noise(enhanced, sample_rate)

        # 2. 스펙트럼 스무딩
        if self.spectral_smoothing:
            enhanced = self._spectral_smooth(enhanced, sample_rate)

        # 3. 다이나믹 레인지 압축
        if self.dynamic_range_compression:
            enhanced = self._compress_dynamic_range(enhanced)

        # 4. 이퀄라이제이션
        if self.equalization:
            enhanced = self._equalize(enhanced, sample_rate)

        # 5. 최종 정규화
        enhanced = self._normalize(enhanced)

        return enhanced

    def _reduce_noise(
        self, audio: np.ndarray, sample_rate: int
    ) -> np.ndarray:
        """
        간단한 노이즈 감소 (스펙트럼 게이팅)

        Args:
            audio: 오디오 데이터
            sample_rate: 샘플링 레이트

        Returns:
            노이즈가 감소된 오디오
        """
        # STFT
        n_fft = 2048
        hop_length = 512

        D = librosa.stft(audio, n_fft=n_fft, hop_length=hop_length)
        magnitude, phase = np.abs(D), np.angle(D)

        # 노이즈 추정 (처음 0.5초를 노이즈로 가정)
        noise_duration = 0.5  # 초
        noise_frames = int(noise_duration * sample_rate / hop_length)
        noise_frames = min(noise_frames, magnitude.shape[1])

        if noise_frames > 0:
            noise_profile = np.mean(magnitude[:, :noise_frames], axis=1, keepdims=True)

            # 스펙트럼 게이팅
            threshold = 1.5  # 노이즈 임계값 배수
            gate = magnitude > (noise_profile * threshold)

            # 부드러운 게이팅 (0~1)
            gate = gate.astype(float)

            # 게이트 적용
            magnitude_gated = magnitude * gate
        else:
            magnitude_gated = magnitude

        # ISTFT
        D_gated = magnitude_gated * np.exp(1j * phase)
        audio_denoised = librosa.istft(D_gated, hop_length=hop_length, length=len(audio))

        return audio_denoised

    def _spectral_smooth(
        self, audio: np.ndarray, sample_rate: int
    ) -> np.ndarray:
        """
        스펙트럼 스무딩 (아티팩트 제거)

        Args:
            audio: 오디오 데이터
            sample_rate: 샘플링 레이트

        Returns:
            스무딩된 오디오
        """
        # STFT
        n_fft = 2048
        hop_length = 512

        D = librosa.stft(audio, n_fft=n_fft, hop_length=hop_length)
        magnitude, phase = np.abs(D), np.angle(D)

        # 시간 축 스무딩 (median filter)
        from scipy.ndimage import median_filter

        magnitude_smoothed = median_filter(magnitude, size=(1, 5))

        # 주파수 축 스무딩 (가우시안 필터)
        from scipy.ndimage import gaussian_filter

        magnitude_smoothed = gaussian_filter(magnitude_smoothed, sigma=(1, 0))

        # ISTFT
        D_smoothed = magnitude_smoothed * np.exp(1j * phase)
        audio_smoothed = librosa.istft(D_smoothed, hop_length=hop_length, length=len(audio))

        return audio_smoothed

    def _compress_dynamic_range(
        self, audio: np.ndarray, threshold: float = -20, ratio: float = 4
    ) -> np.ndarray:
        """
        다이나믹 레인지 압축 (컴프레서)

        Args:
            audio: 오디오 데이터
            threshold: 임계값 (dB)
            ratio: 압축 비율

        Returns:
            압축된 오디오
        """
        # dB로 변환
        eps = 1e-8
        audio_db = 20 * np.log10(np.abs(audio) + eps)

        # 압축
        mask = audio_db > threshold
        compressed_db = audio_db.copy()
        compressed_db[mask] = threshold + (audio_db[mask] - threshold) / ratio

        # 선형 스케일로 복원
        gain = 10 ** ((compressed_db - audio_db) / 20)
        compressed = audio * gain

        return compressed

    def _equalize(
        self, audio: np.ndarray, sample_rate: int
    ) -> np.ndarray:
        """
        이퀄라이제이션 (간단한 high-pass/low-pass)

        Args:
            audio: 오디오 데이터
            sample_rate: 샘플링 레이트

        Returns:
            이퀄라이즈된 오디오
        """
        # High-pass filter (저음 제거, 럼블 제거)
        highpass_freq = 80  # Hz
        sos = signal.butter(
            4, highpass_freq, btype="high", fs=sample_rate, output="sos"
        )
        filtered = signal.sosfilt(sos, audio)

        # Low-pass filter (고음 제한, 노이즈 감소)
        lowpass_freq = 8000  # Hz
        sos = signal.butter(
            4, lowpass_freq, btype="low", fs=sample_rate, output="sos"
        )
        filtered = signal.sosfilt(sos, filtered)

        return filtered

    def _normalize(self, audio: np.ndarray, target_level: float = 0.9) -> np.ndarray:
        """
        오디오 정규화

        Args:
            audio: 오디오 데이터
            target_level: 타겟 레벨 (0~1)

        Returns:
            정규화된 오디오
        """
        max_val = np.abs(audio).max()
        if max_val > 0:
            audio = audio / max_val * target_level

        return audio

    def remove_clicks(
        self, audio: np.ndarray, sample_rate: int
    ) -> np.ndarray:
        """
        클릭 노이즈 제거

        Args:
            audio: 오디오 데이터
            sample_rate: 샘플링 레이트

        Returns:
            클릭이 제거된 오디오
        """
        # 급격한 변화 감지
        diff = np.diff(audio)
        threshold = np.std(diff) * 5

        # 클릭 위치 찾기
        click_indices = np.where(np.abs(diff) > threshold)[0]

        # 클릭 보간
        fixed = audio.copy()
        for idx in click_indices:
            # 주변 값으로 보간
            start = max(0, idx - 2)
            end = min(len(audio), idx + 3)

            if start < idx and idx + 1 < end:
                fixed[idx : idx + 1] = np.mean([fixed[start], fixed[end - 1]])

        return fixed

    def __repr__(self) -> str:
        return (
            f"QualityEnhancer(noise_reduction={self.noise_reduction}, "
            f"spectral_smoothing={self.spectral_smoothing})"
        )
