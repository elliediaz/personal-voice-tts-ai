"""
Waveform Visualization Widget

파형 시각화 위젯
"""

import logging
from typing import Optional

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFrame

from gui.themes.win98.colors import Win98Colors

logger = logging.getLogger(__name__)


class WaveformWidget(QWidget):
    """파형 시각화 위젯"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.audio_data: Optional[np.ndarray] = None
        self.sample_rate: Optional[int] = None

        self._init_ui()

        logger.debug("WaveformWidget 초기화")

    def _init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 3D 오목 효과를 위한 프레임
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Sunken)
        frame.setLineWidth(2)
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(2, 2, 2, 2)

        # Matplotlib Figure (Windows 98 스타일)
        self.figure = Figure(figsize=(10, 4), facecolor=Win98Colors.PLOT_FACE)
        self.canvas = FigureCanvas(self.figure)
        frame_layout.addWidget(self.canvas)

        layout.addWidget(frame)

        # Axes (Windows 98 스타일)
        self.ax = self.figure.add_subplot(111)
        self._apply_win98_style()

        self.figure.tight_layout()

    def _apply_win98_style(self):
        """Windows 98 스타일 적용"""
        self.ax.set_facecolor(Win98Colors.PLOT_BG)
        self.ax.set_xlabel("시간 (초)", color=Win98Colors.PLOT_TEXT)
        self.ax.set_ylabel("진폭", color=Win98Colors.PLOT_TEXT)
        self.ax.set_title("파형", color=Win98Colors.PLOT_TEXT)
        self.ax.tick_params(colors=Win98Colors.PLOT_TEXT)
        self.ax.grid(True, alpha=0.5, color=Win98Colors.PLOT_GRID)

        # 축 테두리 색상
        for spine in self.ax.spines.values():
            spine.set_color(Win98Colors.BORDER_DARK)

    def plot_waveform(self, audio_data: np.ndarray, sample_rate: int):
        """
        파형 그리기

        Args:
            audio_data: 오디오 데이터 (1D 또는 2D numpy array)
            sample_rate: 샘플레이트
        """
        self.audio_data = audio_data
        self.sample_rate = sample_rate

        # 초기화 (Windows 98 스타일 유지)
        self.ax.clear()
        self._apply_win98_style()

        # 스테레오인 경우 모노로 변환
        if audio_data.ndim == 2:
            audio_data = np.mean(audio_data, axis=1)

        # 시간 축 생성
        duration = len(audio_data) / sample_rate
        time = np.linspace(0, duration, len(audio_data))

        # 다운샘플링 (성능 최적화)
        max_points = 10000
        if len(audio_data) > max_points:
            step = len(audio_data) // max_points
            time = time[::step]
            audio_data = audio_data[::step]

        # 파형 그리기 (Windows 98 스타일 - 파란색)
        self.ax.plot(time, audio_data, linewidth=0.5, color=Win98Colors.PLOT_LINE)
        self.ax.set_xlim(0, duration)
        self.ax.set_ylim(-1.0, 1.0)

        self.canvas.draw()

        logger.debug(f"파형 그리기 완료: {len(audio_data)} 샘플, {sample_rate} Hz")

    def clear(self):
        """파형 지우기"""
        self.ax.clear()
        self._apply_win98_style()
        self.canvas.draw()

        logger.debug("파형 지움")
