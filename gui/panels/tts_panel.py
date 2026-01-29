"""
TTS Panel

TTS 패널
"""

import logging
import random
from pathlib import Path
from typing import List, Optional, Dict, Any

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QPushButton,
    QLabel,
    QTextEdit,
    QLineEdit,
    QFileDialog,
    QComboBox,
    QProgressBar,
    QMessageBox,
    QListWidget,
    QCheckBox,
    QSlider,
    QFrame,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from gui.widgets.player import AudioPlayerWidget
from utils.temp_manager import TempFileManager

logger = logging.getLogger(__name__)


# 음성 파라미터 프리셋 정의
VOICE_PRESETS: Dict[str, Optional[Dict[str, int]]] = {
    "기본": {"speed": 100, "pitch": 100, "volume": 100},
    "천천히 또렷하게": {"speed": 70, "pitch": 95, "volume": 100},
    "빠르고 경쾌하게": {"speed": 140, "pitch": 110, "volume": 95},
    "저음 부드럽게": {"speed": 85, "pitch": 70, "volume": 90},
    "고음 활기차게": {"speed": 120, "pitch": 130, "volume": 100},
    "랜덤 음성": None,  # 무작위 값 생성
}

# 미리 듣기용 샘플 텍스트
PREVIEW_SAMPLE_TEXT = "안녕하세요, 음성 테스트입니다."


class TTSWorker(QThread):
    """TTS 작업 워커 스레드"""

    progress = pyqtSignal(int)
    finished = pyqtSignal(dict, bool)  # metadata, auto_play
    error = pyqtSignal(str)

    def __init__(
        self,
        text: str,
        source_files: List[Path],
        output_file: Path,
        backend: str,
        collage: bool = False,
        auto_play: bool = False,
        speech_rate: float = 1.0,
        pitch: float = 1.0,
        volume: float = 1.0,
    ):
        super().__init__()
        self.text = text
        self.source_files = source_files
        self.output_file = output_file
        self.backend = backend
        self.collage = collage
        self.auto_play = auto_play
        self.speech_rate = speech_rate
        self.pitch = pitch
        self.volume = volume

    def _create_backend(self):
        """
        선택된 백엔드에 따라 TTS 엔진 인스턴스를 생성

        Returns:
            BaseTTSEngine: TTS 백엔드 인스턴스
        """
        if self.backend == "gtts":
            from core.tts.backends import GTTSBackend
            # gTTS는 slow 옵션으로 속도 조절 (0.8 미만일 때 slow=True)
            return GTTSBackend(language="ko", slow=(self.speech_rate < 0.8))

        elif self.backend == "pyttsx3":
            from core.tts.backends import Pyttsx3Backend
            # pyttsx3는 WPM (단어/분) 단위 사용, 기본 150에 배율 적용
            return Pyttsx3Backend(
                language="ko",
                speech_rate=int(150 * self.speech_rate),
                volume=self.volume,
            )

        elif self.backend == "edge-tts":
            from core.tts.backends import EdgeTTSBackend
            return EdgeTTSBackend(
                language="ko-KR",
                speech_rate=self.speech_rate,
                pitch=self.pitch,
                volume=self.volume,
            )

        else:
            # 기본값: gTTS
            from core.tts.backends import GTTSBackend
            return GTTSBackend(language="ko")

    def run(self):
        """워커 실행"""
        try:
            tts_backend = self._create_backend()

            if self.collage:
                # TTS-to-Collage 파이프라인
                from algorithms.traditional.mfcc import MFCCSimilarity
                from core.tts.pipeline import TTSPipeline

                sim_algo = MFCCSimilarity()
                pipeline = TTSPipeline(tts_engine=tts_backend, similarity_algorithm=sim_algo)

                self.progress.emit(50)

                metadata = pipeline.synthesize_collage(
                    text=self.text,
                    source_files=self.source_files,
                    output_path=self.output_file,
                )

                self.progress.emit(100)
                self.finished.emit(metadata, self.auto_play)

            else:
                # 일반 TTS
                self.progress.emit(50)

                audio_data, sample_rate = tts_backend.synthesize(
                    text=self.text,
                    output_path=self.output_file,
                )

                self.progress.emit(100)
                self.finished.emit({"output_path": str(self.output_file)}, self.auto_play)

        except Exception as e:
            logger.error(f"TTS 오류: {str(e)}", exc_info=True)
            self.error.emit(str(e))


class TTSPanel(QWidget):
    """TTS 패널"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.source_files: List[Path] = []
        self.output_file: Optional[Path] = None
        self.last_output_path: Optional[Path] = None  # 마지막 생성된 음성 경로

        self._init_ui()

        logger.debug("TTSPanel 초기화")

    def _init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)

        # 텍스트 입력
        text_group = QGroupBox("텍스트 입력")
        text_layout = QVBoxLayout(text_group)

        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("여기에 텍스트를 입력하세요...")
        text_layout.addWidget(self.text_edit)

        layout.addWidget(text_group)

        # TTS 설정
        settings_group = QGroupBox("TTS 설정")
        settings_layout = QVBoxLayout(settings_group)

        # 백엔드 선택
        backend_layout = QHBoxLayout()
        backend_layout.addWidget(QLabel("백엔드:"))
        self.backend_combo = QComboBox()
        self.backend_combo.addItems(["gtts", "pyttsx3", "edge-tts"])
        self.backend_combo.currentTextChanged.connect(self._on_backend_changed)
        backend_layout.addWidget(self.backend_combo)
        backend_layout.addStretch()
        settings_layout.addLayout(backend_layout)

        # 음성 파라미터 그룹
        param_group = QGroupBox("음성 파라미터")
        param_layout = QVBoxLayout(param_group)

        # 프리셋 선택
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("프리셋:"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(list(VOICE_PRESETS.keys()))
        self.preset_combo.currentTextChanged.connect(self._on_preset_changed)
        preset_layout.addWidget(self.preset_combo)
        preset_layout.addStretch()
        param_layout.addLayout(preset_layout)

        # 속도 슬라이더 (50% ~ 200%)
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("속도:"))
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(50, 200)
        self.speed_slider.setValue(100)
        self.speed_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.speed_slider.setTickInterval(25)
        self.speed_slider.valueChanged.connect(self._on_slider_changed)
        speed_layout.addWidget(self.speed_slider)
        self.speed_label = QLabel("1.0x")
        self.speed_label.setMinimumWidth(45)
        speed_layout.addWidget(self.speed_label)
        param_layout.addLayout(speed_layout)

        # 피치 슬라이더 (50% ~ 200%)
        pitch_layout = QHBoxLayout()
        pitch_layout.addWidget(QLabel("피치:"))
        self.pitch_slider = QSlider(Qt.Orientation.Horizontal)
        self.pitch_slider.setRange(50, 200)
        self.pitch_slider.setValue(100)
        self.pitch_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.pitch_slider.setTickInterval(25)
        self.pitch_slider.valueChanged.connect(self._on_slider_changed)
        pitch_layout.addWidget(self.pitch_slider)
        self.pitch_label = QLabel("1.0x")
        self.pitch_label.setMinimumWidth(45)
        pitch_layout.addWidget(self.pitch_label)
        param_layout.addLayout(pitch_layout)

        # 볼륨 슬라이더 (0% ~ 100%)
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("볼륨:"))
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.volume_slider.setTickInterval(25)
        self.volume_slider.valueChanged.connect(self._on_slider_changed)
        volume_layout.addWidget(self.volume_slider)
        self.volume_label = QLabel("100%")
        self.volume_label.setMinimumWidth(45)
        volume_layout.addWidget(self.volume_label)
        param_layout.addLayout(volume_layout)

        # 파라미터 지원 안내 라벨
        self.param_info_label = QLabel("※ gTTS는 속도만 지원합니다 (느리게/보통)")
        self.param_info_label.setStyleSheet("color: #666666; font-size: 10px;")
        param_layout.addWidget(self.param_info_label)

        settings_layout.addWidget(param_group)

        # 콜라주 옵션
        collage_layout = QHBoxLayout()
        collage_layout.addWidget(QLabel("소스 파일 (콜라주용):"))
        self.source_list = QListWidget()
        self.source_list.setMaximumHeight(80)
        collage_layout.addWidget(self.source_list)

        source_btn_layout = QVBoxLayout()
        add_source_btn = QPushButton("추가")
        add_source_btn.clicked.connect(self._on_add_source)
        source_btn_layout.addWidget(add_source_btn)
        remove_source_btn = QPushButton("제거")
        remove_source_btn.clicked.connect(self._on_remove_source)
        source_btn_layout.addWidget(remove_source_btn)
        source_btn_layout.addStretch()
        collage_layout.addLayout(source_btn_layout)

        settings_layout.addLayout(collage_layout)

        # 출력 파일
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("출력 파일:"))
        self.output_edit = QLineEdit()
        self.output_edit.setReadOnly(True)
        output_layout.addWidget(self.output_edit)
        output_btn = QPushButton("찾아보기")
        output_btn.clicked.connect(self._on_select_output)
        output_layout.addWidget(output_btn)
        settings_layout.addLayout(output_layout)

        # 옵션 체크박스
        options_layout = QHBoxLayout()
        self.use_temp_file_checkbox = QCheckBox("임시 파일 사용")
        self.use_temp_file_checkbox.setChecked(True)
        self.use_temp_file_checkbox.setToolTip("체크 시 출력 파일 지정 없이 임시 파일에 저장")
        options_layout.addWidget(self.use_temp_file_checkbox)

        self.auto_play_checkbox = QCheckBox("생성 후 자동 재생")
        self.auto_play_checkbox.setChecked(True)
        self.auto_play_checkbox.setToolTip("체크 시 음성 생성 완료 후 자동으로 재생")
        options_layout.addWidget(self.auto_play_checkbox)

        options_layout.addStretch()
        settings_layout.addLayout(options_layout)

        layout.addWidget(settings_group)

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

        # 바로 듣기 버튼 (강조)
        self.quick_speak_btn = QPushButton("▶ 바로 듣기")
        self.quick_speak_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.quick_speak_btn.setToolTip("텍스트를 즉시 음성으로 변환하고 재생합니다")
        self.quick_speak_btn.clicked.connect(self._on_quick_speak)
        button_layout.addWidget(self.quick_speak_btn)

        # 미리 듣기 버튼
        self.preview_btn = QPushButton("미리 듣기")
        self.preview_btn.setToolTip("샘플 텍스트로 현재 설정을 테스트합니다")
        self.preview_btn.clicked.connect(self._on_preview)
        button_layout.addWidget(self.preview_btn)

        # 다시 듣기 버튼
        self.replay_btn = QPushButton("다시 듣기")
        self.replay_btn.setToolTip("마지막으로 생성된 음성을 다시 재생합니다")
        self.replay_btn.clicked.connect(self._on_replay)
        self.replay_btn.setEnabled(False)  # 처음에는 비활성화
        button_layout.addWidget(self.replay_btn)

        self.speak_btn = QPushButton("음성 생성")
        self.speak_btn.clicked.connect(lambda: self._on_generate_tts(collage=False))
        button_layout.addWidget(self.speak_btn)

        self.collage_btn = QPushButton("콜라주 생성")
        self.collage_btn.clicked.connect(lambda: self._on_generate_tts(collage=True))
        button_layout.addWidget(self.collage_btn)

        layout.addLayout(button_layout)

    def _get_voice_params(self) -> Dict[str, float]:
        """
        현재 슬라이더 값에서 음성 파라미터를 가져옴

        Returns:
            Dict[str, float]: speech_rate, pitch, volume 값
        """
        return {
            "speech_rate": self.speed_slider.value() / 100.0,
            "pitch": self.pitch_slider.value() / 100.0,
            "volume": self.volume_slider.value() / 100.0,
        }

    def _on_slider_changed(self):
        """슬라이더 값 변경 시 라벨 업데이트"""
        speed = self.speed_slider.value()
        pitch = self.pitch_slider.value()
        volume = self.volume_slider.value()

        self.speed_label.setText(f"{speed / 100:.1f}x")
        self.pitch_label.setText(f"{pitch / 100:.1f}x")
        self.volume_label.setText(f"{volume}%")

    def _on_preset_changed(self, preset_name: str):
        """프리셋 선택 시 슬라이더 값 변경"""
        if preset_name == "랜덤 음성":
            # 무작위 값 생성
            speed = random.randint(60, 150)
            pitch = random.randint(60, 150)
            volume = random.randint(70, 100)
        else:
            preset = VOICE_PRESETS.get(preset_name)
            if preset is None:
                return
            speed = preset["speed"]
            pitch = preset["pitch"]
            volume = preset["volume"]

        # 슬라이더 값 설정 (시그널 블록하여 중복 호출 방지)
        self.speed_slider.blockSignals(True)
        self.pitch_slider.blockSignals(True)
        self.volume_slider.blockSignals(True)

        self.speed_slider.setValue(speed)
        self.pitch_slider.setValue(pitch)
        self.volume_slider.setValue(volume)

        self.speed_slider.blockSignals(False)
        self.pitch_slider.blockSignals(False)
        self.volume_slider.blockSignals(False)

        # 라벨 업데이트
        self._on_slider_changed()

        logger.debug(f"프리셋 적용: {preset_name} (속도={speed}, 피치={pitch}, 볼륨={volume})")

    def _on_backend_changed(self, backend_name: str):
        """백엔드 변경 시 파라미터 지원 안내 업데이트"""
        if backend_name == "gtts":
            self.param_info_label.setText("※ gTTS는 속도만 지원합니다 (느리게/보통)")
            self.pitch_slider.setEnabled(False)
            self.volume_slider.setEnabled(False)
        elif backend_name == "pyttsx3":
            self.param_info_label.setText("※ pyttsx3는 속도와 볼륨을 지원합니다")
            self.pitch_slider.setEnabled(False)
            self.volume_slider.setEnabled(True)
        elif backend_name == "edge-tts":
            self.param_info_label.setText("※ Edge-TTS는 모든 파라미터를 지원합니다")
            self.pitch_slider.setEnabled(True)
            self.volume_slider.setEnabled(True)

    def _on_preview(self):
        """미리 듣기: 샘플 텍스트로 현재 설정 테스트"""
        output_path = TempFileManager.create_temp_file(suffix=".wav")
        params = self._get_voice_params()

        self.worker = TTSWorker(
            text=PREVIEW_SAMPLE_TEXT,
            source_files=[],
            output_file=output_path,
            backend=self.backend_combo.currentText(),
            collage=False,
            auto_play=True,
            speech_rate=params["speech_rate"],
            pitch=params["pitch"],
            volume=params["volume"],
        )

        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_tts_finished)
        self.worker.error.connect(self._on_tts_error)

        self._set_buttons_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.worker.start()
        logger.info("미리 듣기 시작")

    def _on_replay(self):
        """다시 듣기: 마지막 생성된 음성 재생"""
        if self.last_output_path and self.last_output_path.exists():
            self.player_widget.load_and_play(self.last_output_path)
            logger.info(f"다시 듣기: {self.last_output_path}")
        else:
            QMessageBox.warning(self, "경고", "재생할 음성이 없습니다.")

    def _set_buttons_enabled(self, enabled: bool):
        """버튼들의 활성화 상태 설정"""
        self.quick_speak_btn.setEnabled(enabled)
        self.preview_btn.setEnabled(enabled)
        self.speak_btn.setEnabled(enabled)
        self.collage_btn.setEnabled(enabled)

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
            "Audio Files (*.wav *.mp3);;All Files (*)",
        )

        if file_path:
            self.output_file = Path(file_path)
            self.output_edit.setText(str(self.output_file))
            logger.info(f"출력 파일 선택: {self.output_file}")

    def _get_output_path(self) -> Optional[Path]:
        """
        출력 파일 경로를 반환합니다.

        임시 파일 사용이 체크되어 있으면 임시 파일 경로를 생성하고,
        그렇지 않으면 사용자가 지정한 출력 파일 경로를 반환합니다.

        Returns:
            Path: 출력 파일 경로, 유효하지 않으면 None
        """
        if self.use_temp_file_checkbox.isChecked():
            return TempFileManager.create_temp_file(suffix=".wav")
        else:
            if not self.output_file:
                QMessageBox.warning(self, "경고", "출력 파일을 선택하거나 '임시 파일 사용'을 체크하세요.")
                return None
            return self.output_file

    def _on_quick_speak(self):
        """바로 듣기: 임시 파일로 생성 후 자동 재생"""
        # 텍스트 검증
        text = self.text_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "경고", "텍스트를 입력하세요.")
            return

        # 임시 파일 경로 생성
        output_path = TempFileManager.create_temp_file(suffix=".wav")
        params = self._get_voice_params()

        # 워커 스레드 생성 (auto_play=True)
        self.worker = TTSWorker(
            text=text,
            source_files=[],
            output_file=output_path,
            backend=self.backend_combo.currentText(),
            collage=False,
            auto_play=True,
            speech_rate=params["speech_rate"],
            pitch=params["pitch"],
            volume=params["volume"],
        )

        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_tts_finished)
        self.worker.error.connect(self._on_tts_error)

        # UI 업데이트
        self._set_buttons_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # 워커 시작
        self.worker.start()

        logger.info("바로 듣기 시작")

    def _on_generate_tts(self, collage: bool = False):
        """TTS 생성"""
        # 검증
        text = self.text_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "경고", "텍스트를 입력하세요.")
            return

        # 출력 경로 결정
        output_path = self._get_output_path()
        if not output_path:
            return

        if collage and not self.source_files:
            QMessageBox.warning(self, "경고", "콜라주를 위해 소스 파일을 추가하세요.")
            return

        # auto_play 옵션 확인
        auto_play = self.auto_play_checkbox.isChecked()
        params = self._get_voice_params()

        # 워커 스레드 생성
        self.worker = TTSWorker(
            text=text,
            source_files=self.source_files,
            output_file=output_path,
            backend=self.backend_combo.currentText(),
            collage=collage,
            auto_play=auto_play,
            speech_rate=params["speech_rate"],
            pitch=params["pitch"],
            volume=params["volume"],
        )

        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_tts_finished)
        self.worker.error.connect(self._on_tts_error)

        # UI 업데이트
        self._set_buttons_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # 워커 시작
        self.worker.start()

        logger.info(f"TTS 생성 시작 (collage={collage}, auto_play={auto_play})")

    def _on_progress(self, value):
        """진행률 업데이트"""
        self.progress_bar.setValue(value)

    def _on_tts_finished(self, metadata: dict, auto_play: bool):
        """TTS 생성 완료"""
        self._set_buttons_enabled(True)
        self.progress_bar.setVisible(False)

        # 출력 경로 가져오기
        output_path = Path(metadata.get("output_path", ""))
        self.last_output_path = output_path  # 마지막 생성 경로 저장
        self.replay_btn.setEnabled(True)  # 다시 듣기 버튼 활성화

        # 임시 파일이 아닌 경우에만 완료 메시지 표시
        if not self.use_temp_file_checkbox.isChecked() or not auto_play:
            QMessageBox.information(self, "완료", f"음성 생성이 완료되었습니다.\n\n출력: {output_path}")

        # 결과 플레이어 로드 (및 자동 재생)
        if auto_play:
            self.player_widget.load_and_play(output_path)
        else:
            self.player_widget.load_audio(output_path)

        logger.info(f"TTS 생성 완료 (auto_play={auto_play})")

    def _on_tts_error(self, error_msg):
        """TTS 생성 오류"""
        self._set_buttons_enabled(True)
        self.progress_bar.setVisible(False)

        QMessageBox.critical(self, "오류", f"TTS 생성 실패:\n\n{error_msg}")

        logger.error(f"TTS 오류: {error_msg}")
