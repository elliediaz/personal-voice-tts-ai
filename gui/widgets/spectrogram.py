"""
Spectrogram Visualization Widget

스펙트로그램 시각화 위젯
"""

import logging
from typing import Optional

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QWidget, QVBoxLayout

logger = logging.getLogger(__name__)


class SpectrogramWidget(QWidget):
    """스펙트로그램 시각화 위젯"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.audio_data: Optional[np.ndarray] = None
        self.sample_rate: Optional[int] = None

        self._init_ui()

        logger.debug("SpectrogramWidget 초기화")

    def _init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)

        # Matplotlib Figure
        self.figure = Figure(figsize=(10, 4))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        # Axes
        self.ax = self.figure.add_subplot(111)
        self.ax.set_xlabel("시간 (초)")
        self.ax.set_ylabel("주파수 (Hz)")
        self.ax.set_title("스펙트로그램")

        self.figure.tight_layout()

    def plot_spectrogram(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        n_fft: int = 2048,
        hop_length: int = 512,
    ):
        """
        스펙트로그램 그리기

        Args:
            audio_data: 오디오 데이터 (1D 또는 2D numpy array)
            sample_rate: 샘플레이트
            n_fft: FFT 윈도우 크기
            hop_length: Hop 길이
        """
        self.audio_data = audio_data
        self.sample_rate = sample_rate

        # 초기화
        self.ax.clear()
        self.ax.set_xlabel("시간 (초)")
        self.ax.set_ylabel("주파수 (Hz)")
        self.ax.set_title("스펙트로그램")

        # 스테레오인 경우 모노로 변환
        if audio_data.ndim == 2:
            audio_data = np.mean(audio_data, axis=1)

        # 스펙트로그램 계산
        try:
            import librosa
            import librosa.display

            # STFT 계산
            D = librosa.stft(audio_data, n_fft=n_fft, hop_length=hop_length)
            S_db = librosa.amplitude_to_db(np.abs(D), ref=np.max)

            # 스펙트로그램 그리기
            img = librosa.display.specshow(
                S_db,
                sr=sample_rate,
                hop_length=hop_length,
                x_axis="time",
                y_axis="hz",
                ax=self.ax,
                cmap="viridis",
            )

            self.figure.colorbar(img, ax=self.ax, format="%+2.0f dB")

        except ImportError:
            # librosa가 없는 경우 matplotlib의 specgram 사용
            self.ax.specgram(
                audio_data,
                Fs=sample_rate,
                NFFT=n_fft,
                noverlap=n_fft - hop_length,
                cmap="viridis",
            )

        self.canvas.draw()

        logger.debug(f"스펙트로그램 그리기 완료: {sample_rate} Hz")

    def clear(self):
        """스펙트로그램 지우기"""
        self.ax.clear()
        self.ax.set_xlabel("시간 (초)")
        self.ax.set_ylabel("주파수 (Hz)")
        self.ax.set_title("스펙트로그램")
        self.canvas.draw()

        logger.debug("스펙트로그램 지움")
