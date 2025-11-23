"""
Batch Processing Panel

배치 처리 패널
"""

import logging
from pathlib import Path
from typing import List

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
    QTextEdit,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

logger = logging.getLogger(__name__)


class BatchWorker(QThread):
    """배치 처리 워커 스레드"""

    progress = pyqtSignal(int, int)  # current, total
    job_finished = pyqtSignal(str)  # job_id
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(
        self,
        workflow: str,
        input_file: Path,
        source_files: List[Path],
        output_dir: Path,
    ):
        super().__init__()
        self.workflow = workflow
        self.input_file = input_file
        self.source_files = source_files
        self.output_dir = output_dir

    def run(self):
        """워커 실행"""
        try:
            from core.batch.processor import BatchProcessor

            # 입력 파일 읽기
            with open(self.input_file, 'r', encoding='utf-8') as f:
                inputs = [line.strip() for line in f if line.strip()]

            # 배치 프로세서 생성
            processor = BatchProcessor(
                max_workers=4,
                use_processes=False,
                continue_on_error=True,
                show_progress=False,
            )

            # 워크플로에 따라 작업 생성
            if self.workflow == "tts_collage":
                from core.tts.backends import GTTSBackend
                from algorithms.traditional.mfcc import MFCCSimilarity
                from core.tts.pipeline import TTSPipeline

                tts_backend = GTTSBackend(language="ko")
                sim_algo = MFCCSimilarity()
                pipeline = TTSPipeline(tts_engine=tts_backend, similarity_algorithm=sim_algo)

                for i, text in enumerate(inputs, 1):
                    output_path = self.output_dir / f"output_{i:03d}.wav"
                    processor.add_job(
                        job_id=f"tts_collage_{i}",
                        func=pipeline.synthesize_collage,
                        kwargs={
                            "text": text,
                            "source_files": self.source_files,
                            "output_path": output_path,
                        },
                        priority=0,
                    )

                    self.progress.emit(0, len(inputs))

            # 처리 실행
            summary = processor.process_all()

            self.finished.emit(summary)

        except Exception as e:
            logger.error(f"배치 처리 오류: {str(e)}", exc_info=True)
            self.error.emit(str(e))


class BatchPanel(QWidget):
    """배치 처리 패널"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.input_file: Path = None
        self.source_files: List[Path] = []
        self.output_dir: Path = None

        self._init_ui()

        logger.debug("BatchPanel 초기화")

    def _init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)

        # 워크플로 선택
        workflow_group = QGroupBox("워크플로")
        workflow_layout = QHBoxLayout(workflow_group)
        workflow_layout.addWidget(QLabel("워크플로:"))
        self.workflow_combo = QComboBox()
        self.workflow_combo.addItems(["tts_collage", "audio_matching", "batch_synthesis"])
        workflow_layout.addWidget(self.workflow_combo)
        workflow_layout.addStretch()
        layout.addWidget(workflow_group)

        # 파일 선택
        file_group = QGroupBox("파일 선택")
        file_layout = QVBoxLayout(file_group)

        # 입력 파일
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("입력 파일:"))
        self.input_edit = QLineEdit()
        self.input_edit.setReadOnly(True)
        input_layout.addWidget(self.input_edit)
        input_btn = QPushButton("찾아보기")
        input_btn.clicked.connect(self._on_select_input)
        input_layout.addWidget(input_btn)
        file_layout.addLayout(input_layout)

        # 소스 파일
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("소스 파일:"))
        self.source_list = QListWidget()
        self.source_list.setMaximumHeight(80)
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

        # 출력 디렉토리
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("출력 디렉토리:"))
        self.output_edit = QLineEdit()
        self.output_edit.setReadOnly(True)
        output_layout.addWidget(self.output_edit)
        output_btn = QPushButton("찾아보기")
        output_btn.clicked.connect(self._on_select_output)
        output_layout.addWidget(output_btn)
        file_layout.addLayout(output_layout)

        layout.addWidget(file_group)

        # 진행률
        progress_group = QGroupBox("진행 상황")
        progress_layout = QVBoxLayout(progress_group)

        self.status_label = QLabel("대기 중")
        progress_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        progress_layout.addWidget(self.log_text)

        layout.addWidget(progress_group)

        # 버튼
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.start_btn = QPushButton("시작")
        self.start_btn.clicked.connect(self._on_start_batch)
        button_layout.addWidget(self.start_btn)

        self.cancel_btn = QPushButton("취소")
        self.cancel_btn.setEnabled(False)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def _on_select_input(self):
        """입력 파일 선택"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "입력 파일 선택 (텍스트 파일)",
            str(Path.home()),
            "Text Files (*.txt);;All Files (*)",
        )

        if file_path:
            self.input_file = Path(file_path)
            self.input_edit.setText(str(self.input_file))
            logger.info(f"입력 파일 선택: {self.input_file}")

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
        """출력 디렉토리 선택"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "출력 디렉토리 선택",
            str(Path.home()),
        )

        if dir_path:
            self.output_dir = Path(dir_path)
            self.output_edit.setText(str(self.output_dir))
            logger.info(f"출력 디렉토리 선택: {self.output_dir}")

    def _on_start_batch(self):
        """배치 처리 시작"""
        # 검증
        if not self.input_file:
            QMessageBox.warning(self, "경고", "입력 파일을 선택하세요.")
            return

        if not self.source_files:
            QMessageBox.warning(self, "경고", "소스 파일을 추가하세요.")
            return

        if not self.output_dir:
            QMessageBox.warning(self, "경고", "출력 디렉토리를 선택하세요.")
            return

        # 출력 디렉토리 생성
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 워커 스레드 생성
        self.worker = BatchWorker(
            workflow=self.workflow_combo.currentText(),
            input_file=self.input_file,
            source_files=self.source_files,
            output_dir=self.output_dir,
        )

        self.worker.progress.connect(self._on_progress)
        self.worker.job_finished.connect(self._on_job_finished)
        self.worker.finished.connect(self._on_batch_finished)
        self.worker.error.connect(self._on_batch_error)

        # UI 업데이트
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.status_label.setText("처리 중...")
        self.progress_bar.setValue(0)
        self.log_text.clear()

        # 워커 시작
        self.worker.start()

        logger.info("배치 처리 시작")

    def _on_progress(self, current, total):
        """진행률 업데이트"""
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)
            self.status_label.setText(f"처리 중... ({current}/{total})")

    def _on_job_finished(self, job_id):
        """작업 완료"""
        self.log_text.append(f"완료: {job_id}")

    def _on_batch_finished(self, summary):
        """배치 처리 완료"""
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.status_label.setText("완료")
        self.progress_bar.setValue(100)

        result_msg = (
            f"배치 처리가 완료되었습니다.\n\n"
            f"전체: {summary['total_count']}\n"
            f"성공: {summary['success_count']}\n"
            f"실패: {summary['error_count']}\n"
            f"성공률: {summary['success_rate']:.1f}%\n"
            f"소요 시간: {summary['total_time']:.2f}초"
        )

        QMessageBox.information(self, "완료", result_msg)

        self.log_text.append("\n" + result_msg)

        logger.info("배치 처리 완료")

    def _on_batch_error(self, error_msg):
        """배치 처리 오류"""
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.status_label.setText("오류")

        QMessageBox.critical(self, "오류", f"배치 처리 실패:\n\n{error_msg}")

        self.log_text.append(f"\n오류: {error_msg}")

        logger.error(f"배치 처리 오류: {error_msg}")
