"""
Audio Analysis Module

오디오 분석 기능을 제공합니다.
스펙트로그램, MFCC, 에너지, 제로크로싱율 등의 특징을 추출합니다.
"""

from typing import Optional, Tuple

import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np

from config import get_config
from utils.logging import get_logger

logger = get_logger(__name__)


class AudioAnalyzer:
    """
    오디오 분석 기능을 제공하는 클래스.

    스펙트로그램, 멜-스펙트로그램, MFCC, 에너지 등의 특징을 추출합니다.
    """

    def __init__(
        self,
        n_fft: Optional[int] = None,
        hop_length: Optional[int] = None,
        window: Optional[str] = None,
        n_mels: Optional[int] = None,
        n_mfcc: Optional[int] = None,
        fmin: Optional[float] = None,
        fmax: Optional[float] = None,
    ):
        """
        AudioAnalyzer를 초기화합니다.

        Args:
            n_fft: FFT 윈도우 크기
            hop_length: 홉 길이
            window: 윈도우 함수
            n_mels: 멜 필터뱅크 수
            n_mfcc: MFCC 계수 개수
            fmin: 최소 주파수
            fmax: 최대 주파수
        """
        config = get_config()
        analysis_config = config.audio.analysis

        self.n_fft = n_fft or analysis_config.get('n_fft', 2048)
        self.hop_length = hop_length or analysis_config.get('hop_length', 512)
        self.window = window or analysis_config.get('window', 'hann')
        self.n_mels = n_mels or analysis_config.get('n_mels', 128)
        self.n_mfcc = n_mfcc or analysis_config.get('n_mfcc', 13)
        self.fmin = fmin or analysis_config.get('fmin', 0)
        self.fmax = fmax or analysis_config.get('fmax', 8000)

    def compute_spectrogram(
        self,
        audio: np.ndarray,
        sr: int,
    ) -> np.ndarray:
        """
        스펙트로그램을 계산합니다.

        Args:
            audio: 오디오 데이터
            sr: 샘플링 레이트

        Returns:
            np.ndarray: 스펙트로그램 (dB 스케일)
        """
        logger.debug("스펙트로그램 계산 중...")

        # STFT 계산
        stft = librosa.stft(
            audio,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
            window=self.window,
        )

        # 크기를 dB 스케일로 변환
        spectrogram = librosa.amplitude_to_db(np.abs(stft), ref=np.max)

        return spectrogram

    def compute_mel_spectrogram(
        self,
        audio: np.ndarray,
        sr: int,
    ) -> np.ndarray:
        """
        멜-스펙트로그램을 계산합니다.

        Args:
            audio: 오디오 데이터
            sr: 샘플링 레이트

        Returns:
            np.ndarray: 멜-스펙트로그램 (dB 스케일)
        """
        logger.debug("멜-스펙트로그램 계산 중...")

        # 멜-스펙트로그램 계산
        mel_spec = librosa.feature.melspectrogram(
            y=audio,
            sr=sr,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
            window=self.window,
            n_mels=self.n_mels,
            fmin=self.fmin,
            fmax=self.fmax,
        )

        # dB 스케일로 변환
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)

        return mel_spec_db

    def compute_mfcc(
        self,
        audio: np.ndarray,
        sr: int,
    ) -> np.ndarray:
        """
        MFCC (Mel-Frequency Cepstral Coefficients)를 계산합니다.

        Args:
            audio: 오디오 데이터
            sr: 샘플링 레이트

        Returns:
            np.ndarray: MFCC 특징 (shape: (n_mfcc, frames))
        """
        logger.debug(f"MFCC 계산 중 (n_mfcc={self.n_mfcc})...")

        mfcc = librosa.feature.mfcc(
            y=audio,
            sr=sr,
            n_mfcc=self.n_mfcc,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
            window=self.window,
            n_mels=self.n_mels,
            fmin=self.fmin,
            fmax=self.fmax,
        )

        return mfcc

    def compute_energy(
        self,
        audio: np.ndarray,
    ) -> np.ndarray:
        """
        RMS 에너지를 계산합니다.

        Args:
            audio: 오디오 데이터

        Returns:
            np.ndarray: RMS 에너지 (shape: (frames,))
        """
        logger.debug("RMS 에너지 계산 중...")

        energy = librosa.feature.rms(
            y=audio,
            frame_length=self.n_fft,
            hop_length=self.hop_length,
        )[0]

        return energy

    def compute_zero_crossing_rate(
        self,
        audio: np.ndarray,
    ) -> np.ndarray:
        """
        제로크로싱율을 계산합니다.

        Args:
            audio: 오디오 데이터

        Returns:
            np.ndarray: 제로크로싱율 (shape: (frames,))
        """
        logger.debug("제로크로싱율 계산 중...")

        zcr = librosa.feature.zero_crossing_rate(
            audio,
            frame_length=self.n_fft,
            hop_length=self.hop_length,
        )[0]

        return zcr

    def compute_spectral_centroid(
        self,
        audio: np.ndarray,
        sr: int,
    ) -> np.ndarray:
        """
        스펙트럼 중심을 계산합니다.

        Args:
            audio: 오디오 데이터
            sr: 샘플링 레이트

        Returns:
            np.ndarray: 스펙트럼 중심 (Hz, shape: (frames,))
        """
        logger.debug("스펙트럼 중심 계산 중...")

        centroid = librosa.feature.spectral_centroid(
            y=audio,
            sr=sr,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
            window=self.window,
        )[0]

        return centroid

    def compute_spectral_rolloff(
        self,
        audio: np.ndarray,
        sr: int,
        roll_percent: float = 0.85,
    ) -> np.ndarray:
        """
        스펙트럼 롤오프를 계산합니다.

        Args:
            audio: 오디오 데이터
            sr: 샘플링 레이트
            roll_percent: 롤오프 비율 (0.0 ~ 1.0)

        Returns:
            np.ndarray: 스펙트럼 롤오프 (Hz, shape: (frames,))
        """
        logger.debug(f"스펙트럼 롤오프 계산 중 (roll_percent={roll_percent})...")

        rolloff = librosa.feature.spectral_rolloff(
            y=audio,
            sr=sr,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
            window=self.window,
            roll_percent=roll_percent,
        )[0]

        return rolloff

    def visualize_waveform(
        self,
        audio: np.ndarray,
        sr: int,
        title: str = "Waveform",
        figsize: Tuple[int, int] = (12, 4),
    ) -> plt.Figure:
        """
        파형을 시각화합니다.

        Args:
            audio: 오디오 데이터
            sr: 샘플링 레이트
            title: 그래프 제목
            figsize: 그림 크기

        Returns:
            plt.Figure: matplotlib Figure 객체
        """
        logger.debug("파형 시각화 중...")

        fig, ax = plt.subplots(figsize=figsize)

        librosa.display.waveshow(audio, sr=sr, ax=ax)
        ax.set_title(title)
        ax.set_xlabel("시간 (초)")
        ax.set_ylabel("진폭")
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        return fig

    def visualize_spectrogram(
        self,
        spectrogram: np.ndarray,
        sr: int,
        title: str = "Spectrogram",
        figsize: Tuple[int, int] = (12, 6),
    ) -> plt.Figure:
        """
        스펙트로그램을 시각화합니다.

        Args:
            spectrogram: 스펙트로그램 데이터
            sr: 샘플링 레이트
            title: 그래프 제목
            figsize: 그림 크기

        Returns:
            plt.Figure: matplotlib Figure 객체
        """
        logger.debug("스펙트로그램 시각화 중...")

        config = get_config()
        colormap = config.visualization.colormap

        fig, ax = plt.subplots(figsize=figsize)

        img = librosa.display.specshow(
            spectrogram,
            sr=sr,
            hop_length=self.hop_length,
            x_axis='time',
            y_axis='hz',
            ax=ax,
            cmap=colormap,
        )

        ax.set_title(title)
        ax.set_xlabel("시간 (초)")
        ax.set_ylabel("주파수 (Hz)")

        fig.colorbar(img, ax=ax, format='%+2.0f dB')
        plt.tight_layout()

        return fig

    def visualize_mel_spectrogram(
        self,
        mel_spectrogram: np.ndarray,
        sr: int,
        title: str = "Mel Spectrogram",
        figsize: Tuple[int, int] = (12, 6),
    ) -> plt.Figure:
        """
        멜-스펙트로그램을 시각화합니다.

        Args:
            mel_spectrogram: 멜-스펙트로그램 데이터
            sr: 샘플링 레이트
            title: 그래프 제목
            figsize: 그림 크기

        Returns:
            plt.Figure: matplotlib Figure 객체
        """
        logger.debug("멜-스펙트로그램 시각화 중...")

        config = get_config()
        colormap = config.visualization.colormap

        fig, ax = plt.subplots(figsize=figsize)

        img = librosa.display.specshow(
            mel_spectrogram,
            sr=sr,
            hop_length=self.hop_length,
            x_axis='time',
            y_axis='mel',
            ax=ax,
            cmap=colormap,
            fmin=self.fmin,
            fmax=self.fmax,
        )

        ax.set_title(title)
        ax.set_xlabel("시간 (초)")
        ax.set_ylabel("멜 주파수")

        fig.colorbar(img, ax=ax, format='%+2.0f dB')
        plt.tight_layout()

        return fig


__all__ = ["AudioAnalyzer"]
