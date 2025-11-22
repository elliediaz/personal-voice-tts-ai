"""
Settings Dialog

설정 대화상자
"""

import logging
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QWidget,
    QGroupBox,
    QLabel,
    QLineEdit,
    QSpinBox,
    QComboBox,
    QCheckBox,
    QPushButton,
    QDialogButtonBox,
)
from PyQt6.QtCore import Qt

logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    """설정 대화상자"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("설정")
        self.setMinimumSize(600, 400)

        self._init_ui()

        logger.debug("SettingsDialog 초기화")

    def _init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)

        # 탭 위젯
        tab_widget = QTabWidget()

        # 일반 설정
        general_tab = self._create_general_tab()
        tab_widget.addTab(general_tab, "일반")

        # 오디오 설정
        audio_tab = self._create_audio_tab()
        tab_widget.addTab(audio_tab, "오디오")

        # 알고리즘 설정
        algorithm_tab = self._create_algorithm_tab()
        tab_widget.addTab(algorithm_tab, "알고리즘")

        layout.addWidget(tab_widget)

        # 버튼
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _create_general_tab(self) -> QWidget:
        """일반 설정 탭"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 애플리케이션 설정
        app_group = QGroupBox("애플리케이션")
        app_layout = QVBoxLayout(app_group)

        # 언어
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("언어:"))
        lang_combo = QComboBox()
        lang_combo.addItems(["한국어", "English"])
        lang_layout.addWidget(lang_combo)
        lang_layout.addStretch()
        app_layout.addLayout(lang_layout)

        # 테마
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("테마:"))
        theme_combo = QComboBox()
        theme_combo.addItems(["라이트", "다크"])
        theme_layout.addWidget(theme_combo)
        theme_layout.addStretch()
        app_layout.addLayout(theme_layout)

        layout.addWidget(app_group)

        # 성능 설정
        perf_group = QGroupBox("성능")
        perf_layout = QVBoxLayout(perf_group)

        # 워커 수
        workers_layout = QHBoxLayout()
        workers_layout.addWidget(QLabel("최대 워커 수:"))
        workers_spin = QSpinBox()
        workers_spin.setRange(1, 16)
        workers_spin.setValue(4)
        workers_layout.addWidget(workers_spin)
        workers_layout.addStretch()
        perf_layout.addLayout(workers_layout)

        # GPU 사용
        gpu_check = QCheckBox("GPU 사용 (사용 가능한 경우)")
        perf_layout.addWidget(gpu_check)

        layout.addWidget(perf_group)

        layout.addStretch()

        return widget

    def _create_audio_tab(self) -> QWidget:
        """오디오 설정 탭"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 오디오 장치
        device_group = QGroupBox("오디오 장치")
        device_layout = QVBoxLayout(device_group)

        # 출력 장치
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("출력 장치:"))
        output_combo = QComboBox()
        output_combo.addItems(["기본 장치"])
        output_layout.addWidget(output_combo)
        device_layout.addLayout(output_layout)

        layout.addWidget(device_group)

        # 품질 설정
        quality_group = QGroupBox("품질")
        quality_layout = QVBoxLayout(quality_group)

        # 샘플레이트
        sr_layout = QHBoxLayout()
        sr_layout.addWidget(QLabel("샘플레이트:"))
        sr_combo = QComboBox()
        sr_combo.addItems(["16000 Hz", "22050 Hz", "44100 Hz", "48000 Hz"])
        sr_combo.setCurrentText("22050 Hz")
        sr_layout.addWidget(sr_combo)
        sr_layout.addStretch()
        quality_layout.addLayout(sr_layout)

        # 비트 깊이
        bit_layout = QHBoxLayout()
        bit_layout.addWidget(QLabel("비트 깊이:"))
        bit_combo = QComboBox()
        bit_combo.addItems(["16-bit", "24-bit", "32-bit float"])
        bit_combo.setCurrentText("16-bit")
        bit_layout.addWidget(bit_combo)
        bit_layout.addStretch()
        quality_layout.addLayout(bit_layout)

        layout.addWidget(quality_group)

        layout.addStretch()

        return widget

    def _create_algorithm_tab(self) -> QWidget:
        """알고리즘 설정 탭"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 유사도 알고리즘
        similarity_group = QGroupBox("유사도 알고리즘")
        similarity_layout = QVBoxLayout(similarity_group)

        # 기본 알고리즘
        algo_layout = QHBoxLayout()
        algo_layout.addWidget(QLabel("기본 알고리즘:"))
        algo_combo = QComboBox()
        algo_combo.addItems(["mfcc", "spectral", "hybrid", "ai_embedding"])
        algo_layout.addWidget(algo_combo)
        algo_layout.addStretch()
        similarity_layout.addLayout(algo_layout)

        # 임계값
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("유사도 임계값:"))
        threshold_spin = QSpinBox()
        threshold_spin.setRange(0, 100)
        threshold_spin.setValue(50)
        threshold_spin.setSuffix("%")
        threshold_layout.addWidget(threshold_spin)
        threshold_layout.addStretch()
        similarity_layout.addLayout(threshold_layout)

        layout.addWidget(similarity_group)

        # 합성 설정
        synthesis_group = QGroupBox("합성")
        synthesis_layout = QVBoxLayout(synthesis_group)

        # 크로스페이드
        crossfade_layout = QHBoxLayout()
        crossfade_layout.addWidget(QLabel("크로스페이드 길이:"))
        crossfade_spin = QSpinBox()
        crossfade_spin.setRange(10, 500)
        crossfade_spin.setValue(50)
        crossfade_spin.setSuffix(" ms")
        crossfade_layout.addWidget(crossfade_spin)
        crossfade_layout.addStretch()
        synthesis_layout.addLayout(crossfade_layout)

        # 피치 조정
        pitch_check = QCheckBox("자동 피치 조정")
        pitch_check.setChecked(True)
        synthesis_layout.addWidget(pitch_check)

        # 템포 조정
        tempo_check = QCheckBox("자동 템포 조정")
        tempo_check.setChecked(True)
        synthesis_layout.addWidget(tempo_check)

        # 품질 향상
        enhance_check = QCheckBox("품질 향상 적용")
        enhance_check.setChecked(True)
        synthesis_layout.addWidget(enhance_check)

        layout.addWidget(synthesis_group)

        layout.addStretch()

        return widget
