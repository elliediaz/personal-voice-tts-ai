"""
Synthesis Panel

오디오 합성 패널
"""

import logging
from pathlib import Path
from typing import List, Optional

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QPushButton,
    QLabel,
    QLineEdit,
    QFileDialog,
    QComboBox,
    QProgressBar,
    QMessageBox,
    QListWidget,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from gui.widgets.player import AudioPlayerWidget
from gui.widgets.waveform import WaveformWidget
from gui.widgets.spectrogram import SpectrogramWidget

logger = logging.getLogger(__name__)


class SynthesisWorker(QThread):
    """합성 작업 워커 스레드"""

    progress = pyqtSignal(int)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(
        self,
        target_file: Path,
        source_files: List[Path],
        output_file: Path,
        algorithm: str,
    ):
        super().__init__()
        self.target_file = target_file
        self.source_files = source_files
        self.output_file = output_file
        self.algorithm = algorithm

    def run(self):
        """워커 실행"""
        try:
            from core.synthesis.engine import CollageEngine
            from algorithms.traditional.mfcc import MFCCSimilarity
            from algorithms.ai_based.hybrid import HybridSimilarity

            # 알고리즘 선택
            if self.algorithm == "mfcc":
                sim_algo = MFCCSimilarity()
            elif self.algorithm == "hybrid":
                sim_algo = HybridSimilarity()
            else:
                sim_algo = MFCCSimilarity()

            # 합성 엔진
            engine = CollageEngine(similarity_algorithm=sim_algo)

            # 합성 실행
            self.progress.emit(50)

            metadata = engine.synthesize_from_file(
                target_file=self.target_file,
                source_files=self.source_files,
                output_path=self.output_file,
            )

            self.progress.emit(100)
            self.finished.emit(metadata)

        except Exception as e:
            logger.error(f"합성 오류: {str(e)}", exc_info=True)
            self.error.emit(str(e))


class SynthesisPanel(QWidget):
    """오디오 합성 패널"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.target_file: Optional[Path] = None
        self.source_files: List[Path] = []
        self.output_file: Optional[Path] = None

        self._init_ui()

        logger.debug("SynthesisPanel 초기화")

    def _init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)

        # 파일 선택 그룹
        file_group = QGroupBox("파일 선택")
        file_layout = QVBoxLayout(file_group)

        # 타겟 파일
        target_layout = QHBoxLayout()
        target_layout.addWidget(QLabel("타겟 파일:"))
        self.target_edit = QLineEdit()
        self.target_edit.setReadOnly(True)
        target_layout.addWidget(self.target_edit)
        target_btn = QPushButton("찾아보기")
        target_btn.clicked.connect(self._on_select_target)
        target_layout.addWidget(target_btn)
        file_layout.addLayout(target_layout)

        # 소스 파일
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("소스 파일:"))
        self.source_list = QListWidget()
        self.source_list.setMaximumHeight(100)
        source_layout.addWidget(self.source_list)
        source_btn_layout = QVBoxLayout()
        add_source_btn = QPushButton("추가")
        add_source_btn.clicked.connect(self._on_add_source)
        source_btn_layout.addWidget(add_source_btn)
        remove_source_btn = QPushButton("제거")
        remove_source_btn.clicked.connect(self._on_remove_source)
        source_btn_layout.addWidget(remove_source_btn)
        source_btn_layout.addStretch()
        source_layout.addLayout(source_btn_layout)
        file_layout.addLayout(source_layout)

        # 출력 파일
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("출력 파일:"))
        self.output_edit = QLineEdit()
        self.output_edit.setReadOnly(True)
        output_layout.addWidget(self.output_edit)
        output_btn = QPushButton("찾아보기")
        output_btn.clicked.connect(self._on_select_output)
        output_layout.addWidget(output_btn)
        file_layout.addLayout(output_layout)

        layout.addWidget(file_group)

        # 알고리즘 선택
        algo_group = QGroupBox("알고리즘")
        algo_layout = QHBoxLayout(algo_group)
        algo_layout.addWidget(QLabel("유사도 알고리즘:"))
        self.algo_combo = QComboBox()
        self.algo_combo.addItems(["mfcc", "hybrid", "spectral"])
        algo_layout.addWidget(self.algo_combo)
        algo_layout.addStretch()
        layout.addWidget(algo_group)

        # 시각화
        viz_group = QGroupBox("시각화")
        viz_layout = QVBoxLayout(viz_group)

        self.waveform_widget = WaveformWidget()
        viz_layout.addWidget(self.waveform_widget)

        self.spectrogram_widget = SpectrogramWidget()
        viz_layout.addWidget(self.spectrogram_widget)

        layout.addWidget(viz_group)

        # 오디오 플레이어
        player_group = QGroupBox("플레이어")
        player_layout = QVBoxLayout(player_group)
        self.player_widget = AudioPlayerWidget()
        player_layout.addWidget(self.player_widget)
        layout.addWidget(player_group)

        # 진행률
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # 버튼
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.synthesize_btn = QPushButton("합성 시작")
        self.synthesize_btn.clicked.connect(self._on_synthesize)
        button_layout.addWidget(self.synthesize_btn)

        layout.addLayout(button_layout)

    def _on_select_target(self):
        """타겟 파일 선택"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "타겟 오디오 파일 선택",
            str(Path.home()),
            "Audio Files (*.wav *.mp3 *.flac);;All Files (*)",
        )

        if file_path:
            self.target_file = Path(file_path)
            self.target_edit.setText(str(self.target_file))
            logger.info(f"타겟 파일 선택: {self.target_file}")

            # 시각화 및 플레이어 업데이트
            self._load_and_visualize(self.target_file)

    def _on_add_source(self):
        """소스 파일 추가"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "소스 오디오 파일 선택",
            str(Path.home()),
            "Audio Files (*.wav *.mp3 *.flac);;All Files (*)",
        )

        for file_path in file_paths:
            source_file = Path(file_path)
            if source_file not in self.source_files:
                self.source_files.append(source_file)
                self.source_list.addItem(source_file.name)
                logger.info(f"소스 파일 추가: {source_file}")

    def _on_remove_source(self):
        """소스 파일 제거"""
        current_row = self.source_list.currentRow()
        if current_row >= 0:
            removed_file = self.source_files.pop(current_row)
            self.source_list.takeItem(current_row)
            logger.info(f"소스 파일 제거: {removed_file}")

    def _on_select_output(self):
        """출력 파일 선택"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "출력 파일 선택",
            str(Path.home()),
            "Audio Files (*.wav *.mp3 *.flac);;All Files (*)",
        )

        if file_path:
            self.output_file = Path(file_path)
            self.output_edit.setText(str(self.output_file))
            logger.info(f"출력 파일 선택: {self.output_file}")

    def _load_and_visualize(self, audio_file: Path):
        """오디오 로드 및 시각화"""
        try:
            import soundfile as sf

            # 오디오 로드
            audio_data, sample_rate = sf.read(audio_file)

            # 파형 표시
            self.waveform_widget.plot_waveform(audio_data, sample_rate)

            # 스펙트로그램 표시
            self.spectrogram_widget.plot_spectrogram(audio_data, sample_rate)

            # 플레이어 로드
            self.player_widget.load_audio(audio_file)

        except Exception as e:
            logger.error(f"오디오 로드 오류: {str(e)}")
            QMessageBox.critical(self, "오류", f"오디오 로드 실패: {str(e)}")

    def _on_synthesize(self):
        """합성 시작"""
        # 검증
        if not self.target_file:
            QMessageBox.warning(self, "경고", "타겟 파일을 선택하세요.")
            return

        if not self.source_files:
            QMessageBox.warning(self, "경고", "소스 파일을 추가하세요.")
            return

        if not self.output_file:
            QMessageBox.warning(self, "경고", "출력 파일을 선택하세요.")
            return

        # 워커 스레드 생성
        self.worker = SynthesisWorker(
            target_file=self.target_file,
            source_files=self.source_files,
            output_file=self.output_file,
            algorithm=self.algo_combo.currentText(),
        )

        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_synthesis_finished)
        self.worker.error.connect(self._on_synthesis_error)

        # UI 업데이트
        self.synthesize_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # 워커 시작
        self.worker.start()

        logger.info("합성 시작")

    def _on_progress(self, value):
        """진행률 업데이트"""
        self.progress_bar.setValue(value)

    def _on_synthesis_finished(self, metadata):
        """합성 완료"""
        self.synthesize_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        QMessageBox.information(self, "완료", f"합성이 완료되었습니다.\n\n출력: {self.output_file}")

        # 결과 로드 및 시각화
        self._load_and_visualize(self.output_file)

        logger.info("합성 완료")

    def _on_synthesis_error(self, error_msg):
        """합성 오류"""
        self.synthesize_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        QMessageBox.critical(self, "오류", f"합성 실패:\n\n{error_msg}")

        logger.error(f"합성 오류: {error_msg}")
