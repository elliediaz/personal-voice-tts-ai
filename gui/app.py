"""
Main Application

메인 GUI 애플리케이션
"""

import sys
import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QMenuBar,
    QMenu,
    QToolBar,
    QStatusBar,
    QMessageBox,
    QFileDialog,
)
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt, QSettings

from gui.panels.synthesis_panel import SynthesisPanel
from gui.panels.tts_panel import TTSPanel
from gui.panels.batch_panel import BatchPanel
from gui.dialogs.settings import SettingsDialog
from gui.dialogs.help import HelpDialog
from config import get_config

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """메인 윈도우 클래스"""

    def __init__(self):
        super().__init__()

        self.settings = QSettings("PersonalVoiceTTS", "PersonalVoiceTTSAI")
        self.config = get_config()

        self._init_ui()
        self._create_menu_bar()
        self._create_tool_bar()
        self._create_status_bar()
        self._restore_settings()

        logger.info("메인 윈도우 초기화 완료")

    def _init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("Personal Voice TTS AI")
        self.setMinimumSize(1200, 800)

        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 메인 레이아웃
        layout = QVBoxLayout(central_widget)

        # 탭 위젯
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # 합성 패널
        self.synthesis_panel = SynthesisPanel()
        self.tab_widget.addTab(self.synthesis_panel, "오디오 합성")

        # TTS 패널
        self.tts_panel = TTSPanel()
        self.tab_widget.addTab(self.tts_panel, "TTS")

        # 배치 처리 패널
        self.batch_panel = BatchPanel()
        self.tab_widget.addTab(self.batch_panel, "배치 처리")

        logger.debug("UI 초기화 완료")

    def _create_menu_bar(self):
        """메뉴바 생성"""
        menubar = self.menuBar()

        # 파일 메뉴
        file_menu = menubar.addMenu("파일(&F)")

        open_action = QAction("열기(&O)", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._on_open)
        file_menu.addAction(open_action)

        save_action = QAction("저장(&S)", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._on_save)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        exit_action = QAction("종료(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 편집 메뉴
        edit_menu = menubar.addMenu("편집(&E)")

        settings_action = QAction("설정(&S)", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self._on_settings)
        edit_menu.addAction(settings_action)

        # 보기 메뉴
        view_menu = menubar.addMenu("보기(&V)")

        # 도움말 메뉴
        help_menu = menubar.addMenu("도움말(&H)")

        help_action = QAction("도움말(&H)", self)
        help_action.setShortcut("F1")
        help_action.triggered.connect(self._on_help)
        help_menu.addAction(help_action)

        about_action = QAction("정보(&A)", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

        logger.debug("메뉴바 생성 완료")

    def _create_tool_bar(self):
        """툴바 생성"""
        toolbar = QToolBar("메인 툴바")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # 열기 버튼
        open_action = QAction("열기", self)
        open_action.triggered.connect(self._on_open)
        toolbar.addAction(open_action)

        # 저장 버튼
        save_action = QAction("저장", self)
        save_action.triggered.connect(self._on_save)
        toolbar.addAction(save_action)

        toolbar.addSeparator()

        # 설정 버튼
        settings_action = QAction("설정", self)
        settings_action.triggered.connect(self._on_settings)
        toolbar.addAction(settings_action)

        logger.debug("툴바 생성 완료")

    def _create_status_bar(self):
        """상태바 생성"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("준비")

        logger.debug("상태바 생성 완료")

    def _restore_settings(self):
        """설정 복원"""
        # 윈도우 위치 및 크기 복원
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

        # 윈도우 상태 복원
        state = self.settings.value("windowState")
        if state:
            self.restoreState(state)

        logger.debug("설정 복원 완료")

    def _save_settings(self):
        """설정 저장"""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())

        logger.debug("설정 저장 완료")

    def _on_open(self):
        """파일 열기"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "오디오 파일 열기",
            str(Path.home()),
            "Audio Files (*.wav *.mp3 *.flac *.ogg);;All Files (*)",
        )

        if file_path:
            logger.info(f"파일 열기: {file_path}")
            self.status_bar.showMessage(f"파일 열림: {file_path}")

    def _on_save(self):
        """파일 저장"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "저장",
            str(Path.home()),
            "Audio Files (*.wav *.mp3 *.flac);;All Files (*)",
        )

        if file_path:
            logger.info(f"파일 저장: {file_path}")
            self.status_bar.showMessage(f"파일 저장됨: {file_path}")

    def _on_settings(self):
        """설정 대화상자"""
        dialog = SettingsDialog(self)
        dialog.exec()

    def _on_help(self):
        """도움말 대화상자"""
        dialog = HelpDialog(self)
        dialog.exec()

    def _on_about(self):
        """정보 대화상자"""
        QMessageBox.about(
            self,
            "Personal Voice TTS AI 정보",
            "<h2>Personal Voice TTS AI</h2>"
            "<p>버전: 0.7.0</p>"
            "<p>음성 콜라주 및 합성 기반의 고급 TTS 시스템</p>"
            "<p><br></p>"
            "<p>주요 기능:</p>"
            "<ul>"
            "<li>다양한 유사도 검출 알고리즘</li>"
            "<li>고급 오디오 합성</li>"
            "<li>TTS 통합</li>"
            "<li>배치 처리</li>"
            "</ul>",
        )

    def closeEvent(self, event):
        """윈도우 닫기 이벤트"""
        self._save_settings()
        logger.info("애플리케이션 종료")
        event.accept()


def main():
    """메인 함수"""
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # 애플리케이션 생성
    app = QApplication(sys.argv)
    app.setApplicationName("Personal Voice TTS AI")
    app.setOrganizationName("PersonalVoiceTTS")

    # 메인 윈도우 생성 및 표시
    window = MainWindow()
    window.show()

    # 이벤트 루프 실행
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
