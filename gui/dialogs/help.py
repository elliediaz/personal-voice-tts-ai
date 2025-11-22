"""
Help Dialog

도움말 대화상자
"""

import logging
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QTextBrowser,
    QDialogButtonBox,
)
from PyQt6.QtCore import Qt

logger = logging.getLogger(__name__)


class HelpDialog(QDialog):
    """도움말 대화상자"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("도움말")
        self.setMinimumSize(700, 500)

        self._init_ui()

        logger.debug("HelpDialog 초기화")

    def _init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)

        # 텍스트 브라우저
        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True)
        self.text_browser.setHtml(self._get_help_content())
        layout.addWidget(self.text_browser)

        # 버튼
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _get_help_content(self) -> str:
        """도움말 내용"""
        return """
        <h1>Personal Voice TTS AI - 도움말</h1>

        <h2>개요</h2>
        <p>
        Personal Voice TTS AI는 음성 콜라주 및 합성 기반의 고급 TTS 시스템입니다.
        소스 오디오 파일들을 분석하여 타겟 음성과 유사한 구간을 찾아내고,
        이를 지능적으로 콜라주하여 새로운 음성을 합성합니다.
        </p>

        <h2>주요 기능</h2>

        <h3>1. 오디오 합성</h3>
        <ul>
            <li><b>타겟 파일</b>: 재현하려는 목표 오디오 파일</li>
            <li><b>소스 파일</b>: 콜라주에 사용될 오디오 파일들</li>
            <li><b>알고리즘</b>: 유사도 검출 알고리즘 선택
                <ul>
                    <li>mfcc: MFCC 기반 (빠름, 전통적)</li>
                    <li>spectral: 스펙트럼 기반</li>
                    <li>hybrid: 전통적 + AI 하이브리드 (권장)</li>
                </ul>
            </li>
        </ul>

        <h3>2. TTS (Text-to-Speech)</h3>
        <ul>
            <li><b>음성 생성</b>: 텍스트를 음성으로 변환</li>
            <li><b>콜라주 생성</b>: TTS 후 소스 파일로 콜라주 적용</li>
            <li><b>백엔드</b>:
                <ul>
                    <li>gtts: Google TTS (온라인)</li>
                    <li>pyttsx3: 시스템 TTS (오프라인)</li>
                    <li>edge-tts: Microsoft Edge TTS (온라인)</li>
                </ul>
            </li>
        </ul>

        <h3>3. 배치 처리</h3>
        <ul>
            <li><b>입력 파일</b>: 텍스트 파일 (한 줄에 하나씩)</li>
            <li><b>워크플로</b>:
                <ul>
                    <li>tts_collage: 텍스트 → TTS → 콜라주</li>
                    <li>audio_matching: 오디오 간 매칭</li>
                    <li>batch_synthesis: 배치 합성</li>
                </ul>
            </li>
            <li><b>출력</b>: 지정된 디렉토리에 일괄 생성</li>
        </ul>

        <h2>사용 방법</h2>

        <h3>기본 워크플로</h3>
        <ol>
            <li>타겟 오디오 파일 선택</li>
            <li>소스 오디오 파일들 추가</li>
            <li>출력 파일 위치 지정</li>
            <li>알고리즘 선택</li>
            <li>"합성 시작" 버튼 클릭</li>
            <li>결과 확인 및 재생</li>
        </ol>

        <h3>TTS 워크플로</h3>
        <ol>
            <li>텍스트 입력</li>
            <li>백엔드 선택</li>
            <li>(콜라주 시) 소스 파일 추가</li>
            <li>출력 파일 위치 지정</li>
            <li>"음성 생성" 또는 "콜라주 생성" 버튼 클릭</li>
            <li>결과 재생</li>
        </ol>

        <h2>팁</h2>
        <ul>
            <li>고품질 소스 파일을 사용하면 더 좋은 결과를 얻을 수 있습니다</li>
            <li>Hybrid 알고리즘은 전통적 방법과 AI를 결합하여 균형잡힌 결과를 제공합니다</li>
            <li>배치 처리 시 워커 수를 조정하여 성능을 최적화할 수 있습니다</li>
            <li>TTS 콜라주는 다양한 소스를 사용할수록 자연스러운 결과를 얻을 수 있습니다</li>
        </ul>

        <h2>문제 해결</h2>
        <ul>
            <li><b>합성이 너무 느림</b>: 알고리즘을 mfcc로 변경하거나 소스 파일 수를 줄이세요</li>
            <li><b>품질이 낮음</b>: Hybrid 알고리즘을 사용하고 고품질 소스를 추가하세요</li>
            <li><b>TTS 오류</b>: 인터넷 연결을 확인하거나 오프라인 백엔드(pyttsx3)를 사용하세요</li>
        </ul>

        <h2>추가 정보</h2>
        <p>
        자세한 정보는 프로젝트 README 파일을 참조하세요.
        </p>
        """
