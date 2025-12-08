#!/bin/bash
# Personal Voice TTS AI - 실행 스크립트 (Linux/macOS)
# 사용법: ./run.sh [명령어]
#
# 명령어:
#   web      - 웹 서버 실행 (기본값)
#   cli      - CLI 도구 실행
#   test     - 테스트 실행
#   install  - 의존성 설치

set -e

# 프로젝트 루트 디렉토리
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 메시지 출력 함수
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Python 확인
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON=python3
    elif command -v python &> /dev/null; then
        PYTHON=python
    else
        error "Python이 설치되어 있지 않습니다."
        exit 1
    fi

    info "Python 버전: $($PYTHON --version)"
}

# 가상환경 활성화
activate_venv() {
    if [ -d "venv" ]; then
        info "가상환경 활성화..."
        source venv/bin/activate
    elif [ -d ".venv" ]; then
        info "가상환경 활성화..."
        source .venv/bin/activate
    fi
}

# 의존성 설치
install_deps() {
    info "의존성 설치 중..."
    $PYTHON -m pip install --upgrade pip
    $PYTHON -m pip install -r requirements.txt
    info "의존성 설치 완료"
}

# 웹 서버 실행
run_web() {
    info "웹 서버 시작..."
    info "접속 주소: http://localhost:${PORT:-8000}"
    $PYTHON -m uvicorn web.app:app --host ${HOST:-0.0.0.0} --port ${PORT:-8000} --reload
}

# CLI 도구 실행
run_cli() {
    shift # 첫 번째 인자 'cli' 제거
    if [ $# -eq 0 ]; then
        info "사용 가능한 CLI 명령어:"
        echo "  basic     - 기본 오디오 처리"
        echo "  similarity - 유사도 검출"
        echo "  synthesize - 오디오 합성"
        echo "  tts       - TTS 변환"
        echo "  batch     - 배치 처리"
        echo ""
        echo "예시: ./run.sh cli basic info audio.wav"
    else
        $PYTHON -m cli.$@
    fi
}

# 테스트 실행
run_test() {
    info "테스트 실행 중..."
    $PYTHON -m pytest tests/ -v --tb=short
}

# GUI 실행
run_gui() {
    info "GUI 애플리케이션 시작..."
    $PYTHON -m gui.app
}

# 도움말 출력
show_help() {
    echo "Personal Voice TTS AI - 실행 스크립트"
    echo ""
    echo "사용법: ./run.sh [명령어] [옵션]"
    echo ""
    echo "명령어:"
    echo "  web      웹 서버 실행 (기본값)"
    echo "  cli      CLI 도구 실행"
    echo "  gui      GUI 애플리케이션 실행"
    echo "  test     테스트 실행"
    echo "  install  의존성 설치"
    echo "  help     도움말 표시"
    echo ""
    echo "환경변수:"
    echo "  HOST     웹 서버 호스트 (기본값: 0.0.0.0)"
    echo "  PORT     웹 서버 포트 (기본값: 8000)"
    echo ""
    echo "예시:"
    echo "  ./run.sh                    # 웹 서버 실행"
    echo "  ./run.sh web                # 웹 서버 실행"
    echo "  ./run.sh cli basic info a.wav  # CLI 오디오 정보 조회"
    echo "  ./run.sh test               # 테스트 실행"
    echo "  PORT=3000 ./run.sh web      # 3000 포트로 웹 서버 실행"
}

# 메인 실행
main() {
    check_python
    activate_venv

    COMMAND=${1:-web}

    case $COMMAND in
        web)
            run_web
            ;;
        cli)
            run_cli "$@"
            ;;
        gui)
            run_gui
            ;;
        test)
            run_test
            ;;
        install)
            install_deps
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            error "알 수 없는 명령어: $COMMAND"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
