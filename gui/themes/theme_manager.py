"""
Theme Manager

테마 로드 및 적용 관리자
"""

import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import QApplication

logger = logging.getLogger(__name__)


class ThemeManager:
    """테마 관리자 클래스"""

    # 사용 가능한 테마 목록
    AVAILABLE_THEMES = ["win98", "default"]

    def __init__(self, app: QApplication):
        """
        테마 관리자 초기화

        Args:
            app: QApplication 인스턴스
        """
        self.app = app
        self.current_theme: Optional[str] = None
        self._themes_dir = Path(__file__).parent

        logger.debug("ThemeManager 초기화")

    def apply_theme(self, theme_name: str) -> bool:
        """
        테마 적용

        Args:
            theme_name: 테마 이름 ("win98", "default" 등)

        Returns:
            성공 여부
        """
        if theme_name == "default":
            return self._apply_default_theme()
        elif theme_name == "win98":
            return self._apply_win98_theme()
        else:
            logger.warning(f"알 수 없는 테마: {theme_name}")
            return False

    def _apply_default_theme(self) -> bool:
        """기본 테마 적용 (스타일시트 제거)"""
        self.app.setStyleSheet("")
        self.current_theme = "default"
        logger.info("기본 테마 적용")
        return True

    def _apply_win98_theme(self) -> bool:
        """Windows 98 테마 적용"""
        qss_path = self._themes_dir / "win98" / "style.qss"

        if not qss_path.exists():
            logger.error(f"스타일시트 파일을 찾을 수 없음: {qss_path}")
            return False

        try:
            with open(qss_path, "r", encoding="utf-8") as f:
                stylesheet = f.read()

            self.app.setStyleSheet(stylesheet)
            self.current_theme = "win98"
            logger.info("Windows 98 테마 적용 완료")
            return True

        except Exception as e:
            logger.error(f"테마 적용 실패: {e}")
            return False

    def get_current_theme(self) -> Optional[str]:
        """현재 적용된 테마 이름 반환"""
        return self.current_theme

    def get_available_themes(self) -> list:
        """사용 가능한 테마 목록 반환"""
        return self.AVAILABLE_THEMES.copy()

    @staticmethod
    def get_win98_colors():
        """Windows 98 색상 팔레트 반환"""
        from gui.themes.win98.colors import Win98Colors
        return Win98Colors
