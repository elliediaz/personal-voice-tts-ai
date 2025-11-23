"""
Audio Player Widget

오디오 플레이어 위젯
"""

import logging
from pathlib import Path
from typing import Optional

import numpy as np
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QSlider,
    QLabel,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl

logger = logging.getLogger(__name__)


class AudioPlayerWidget(QWidget):
    """오디오 플레이어 위젯"""

    position_changed = pyqtSignal(int)
    duration_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.audio_path: Optional[Path] = None
        self.audio_data: Optional[np.ndarray] = None
        self.sample_rate: Optional[int] = None

        # 미디어 플레이어
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)

        self._init_ui()
        self._connect_signals()

        logger.debug("AudioPlayerWidget 초기화")

    def _init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)

        # 컨트롤 레이아웃
        controls_layout = QHBoxLayout()

        # 재생/일시정지 버튼
        self.play_button = QPushButton("재생")
        self.play_button.setEnabled(False)
        self.play_button.clicked.connect(self._on_play_pause)
        controls_layout.addWidget(self.play_button)

        # 정지 버튼
        self.stop_button = QPushButton("정지")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self._on_stop)
        controls_layout.addWidget(self.stop_button)

        # 시간 라벨
        self.time_label = QLabel("00:00 / 00:00")
        controls_layout.addWidget(self.time_label)

        controls_layout.addStretch()

        # 볼륨 라벨
        volume_label = QLabel("볼륨:")
        controls_layout.addWidget(volume_label)

        # 볼륨 슬라이더
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setMaximumWidth(100)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        controls_layout.addWidget(self.volume_slider)

        layout.addLayout(controls_layout)

        # 시크 슬라이더
        self.seek_slider = QSlider(Qt.Orientation.Horizontal)
        self.seek_slider.setEnabled(False)
        self.seek_slider.sliderMoved.connect(self._on_seek)
        layout.addWidget(self.seek_slider)

        # 초기 볼륨 설정
        self._on_volume_changed(50)

    def _connect_signals(self):
        """시그널 연결"""
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.player.playbackStateChanged.connect(self._on_state_changed)

    def load_audio(self, audio_path: Path):
        """
        오디오 파일 로드

        Args:
            audio_path: 오디오 파일 경로
        """
        self.audio_path = audio_path

        # QMediaPlayer로 로드
        url = QUrl.fromLocalFile(str(audio_path.absolute()))
        self.player.setSource(url)

        # 버튼 활성화
        self.play_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        self.seek_slider.setEnabled(True)

        logger.info(f"오디오 로드: {audio_path}")

    def _on_play_pause(self):
        """재생/일시정지"""
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.play_button.setText("재생")
            logger.debug("일시정지")
        else:
            self.player.play()
            self.play_button.setText("일시정지")
            logger.debug("재생")

    def _on_stop(self):
        """정지"""
        self.player.stop()
        self.play_button.setText("재생")
        logger.debug("정지")

    def _on_seek(self, position):
        """시크"""
        self.player.setPosition(position)

    def _on_volume_changed(self, value):
        """볼륨 변경"""
        self.audio_output.setVolume(value / 100.0)

    def _on_position_changed(self, position):
        """재생 위치 변경"""
        self.seek_slider.setValue(position)
        self._update_time_label()
        self.position_changed.emit(position)

    def _on_duration_changed(self, duration):
        """재생 길이 변경"""
        self.seek_slider.setRange(0, duration)
        self._update_time_label()
        self.duration_changed.emit(duration)

    def _on_state_changed(self, state):
        """재생 상태 변경"""
        if state == QMediaPlayer.PlaybackState.StoppedState:
            self.play_button.setText("재생")

    def _update_time_label(self):
        """시간 라벨 업데이트"""
        position = self.player.position()
        duration = self.player.duration()

        position_str = self._format_time(position)
        duration_str = self._format_time(duration)

        self.time_label.setText(f"{position_str} / {duration_str}")

    def _format_time(self, ms):
        """시간 포맷팅 (밀리초 → MM:SS)"""
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def get_position(self) -> int:
        """현재 재생 위치 (밀리초)"""
        return self.player.position()

    def get_duration(self) -> int:
        """재생 길이 (밀리초)"""
        return self.player.duration()
