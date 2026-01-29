"""
Temp File Manager

임시 파일 관리자 - 싱글톤 패턴으로 구현
종료 시 모든 임시 파일을 자동으로 정리합니다.
"""

import atexit
import tempfile
import uuid
from pathlib import Path
from typing import List, Optional

from utils.logging import get_logger

logger = get_logger(__name__)


class TempFileManager:
    """
    임시 파일 관리자 (싱글톤)

    TTS 등에서 생성한 임시 오디오 파일을 관리하고,
    프로그램 종료 시 자동으로 정리합니다.

    Example:
        >>> temp_path = TempFileManager.create_temp_file(suffix=".wav")
        >>> # 파일 사용...
        >>> TempFileManager.delete_temp_file(temp_path)  # 수동 삭제 (선택)
        >>> # 또는 프로그램 종료 시 자동 삭제
    """

    _temp_files: List[Path] = []
    _temp_dir: Optional[Path] = None
    _initialized: bool = False

    @classmethod
    def _ensure_initialized(cls) -> None:
        """초기화 확인 및 수행"""
        if not cls._initialized:
            # 임시 디렉토리 생성
            cls._temp_dir = Path(tempfile.gettempdir()) / "personal_voice_tts"
            cls._temp_dir.mkdir(parents=True, exist_ok=True)

            # 종료 시 정리 등록
            atexit.register(cls.cleanup_all)

            cls._initialized = True
            logger.debug(f"TempFileManager 초기화 완료: {cls._temp_dir}")

    @classmethod
    def create_temp_file(cls, suffix: str = ".wav", prefix: str = "tts_") -> Path:
        """
        임시 파일 경로를 생성합니다.

        Args:
            suffix: 파일 확장자 (기본값: ".wav")
            prefix: 파일명 접두사 (기본값: "tts_")

        Returns:
            Path: 생성된 임시 파일 경로
        """
        cls._ensure_initialized()

        # 고유한 파일명 생성
        unique_id = uuid.uuid4().hex[:8]
        filename = f"{prefix}{unique_id}{suffix}"
        temp_path = cls._temp_dir / filename

        # 목록에 추가
        cls._temp_files.append(temp_path)

        logger.debug(f"임시 파일 생성: {temp_path}")
        return temp_path

    @classmethod
    def delete_temp_file(cls, path: Path) -> bool:
        """
        임시 파일을 삭제합니다.

        Args:
            path: 삭제할 파일 경로

        Returns:
            bool: 삭제 성공 여부
        """
        try:
            if path.exists():
                path.unlink()
                logger.debug(f"임시 파일 삭제: {path}")

            # 목록에서 제거
            if path in cls._temp_files:
                cls._temp_files.remove(path)

            return True

        except Exception as e:
            logger.warning(f"임시 파일 삭제 실패: {path} - {e}")
            return False

    @classmethod
    def cleanup_all(cls) -> int:
        """
        모든 임시 파일을 정리합니다.

        Returns:
            int: 삭제된 파일 수
        """
        deleted_count = 0

        for temp_path in cls._temp_files.copy():
            try:
                if temp_path.exists():
                    temp_path.unlink()
                    deleted_count += 1
                    logger.debug(f"임시 파일 정리: {temp_path}")
            except Exception as e:
                logger.warning(f"임시 파일 정리 실패: {temp_path} - {e}")

        cls._temp_files.clear()

        if deleted_count > 0:
            logger.info(f"임시 파일 {deleted_count}개 정리 완료")

        return deleted_count

    @classmethod
    def get_temp_dir(cls) -> Path:
        """
        임시 파일 디렉토리 경로를 반환합니다.

        Returns:
            Path: 임시 파일 디렉토리 경로
        """
        cls._ensure_initialized()
        return cls._temp_dir

    @classmethod
    def get_temp_files(cls) -> List[Path]:
        """
        현재 관리 중인 임시 파일 목록을 반환합니다.

        Returns:
            List[Path]: 임시 파일 경로 목록
        """
        return cls._temp_files.copy()


__all__ = ["TempFileManager"]
