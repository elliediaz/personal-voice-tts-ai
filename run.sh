#!/bin/bash
# ============================================================================
# Personal Voice TTS AI - 향상된 실행 스크립트 (Linux/macOS)
# 버전: 1.0.0
# ============================================================================
#
# 사용법: ./run.sh [명령어] [옵션]
#
# 명령어:
#   web      - 웹 서버 실행 (기본값)
#   gui      - GUI 애플리케이션 실행
#   cli      - CLI 도구 실행
#   test     - 테스트 실행
#   install  - 의존성 설치
#   setup    - 환경 설정 (가상환경 생성 + 의존성 설치)
#   clean    - 캐시 및 빌드 파일 정리
#   help     - 도움말 표시
#
# 환경변수:
#   PVTTS_HOST       - 웹 서버 호스트 (기본값: 0.0.0.0)
#   PVTTS_PORT       - 웹 서버 포트 (기본값: 8000)
#   PVTTS_DEBUG      - 디버그 모드 (1로 설정하면 활성화)
#   PVTTS_VENV_NAME  - 가상환경 디렉토리 이름 (기본값: venv)
#   PVTTS_AUTO_SETUP - 자동 환경 설정 (기본값: 1, 0으로 비활성화)
# ============================================================================

set -e

# 프로젝트 루트 디렉토리
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# ============================================================================
# 색상 정의
# ============================================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ============================================================================
# 환경 변수 기본값
# ============================================================================
PVTTS_HOST="${PVTTS_HOST:-0.0.0.0}"
PVTTS_PORT="${PVTTS_PORT:-8000}"
PVTTS_DEBUG="${PVTTS_DEBUG:-0}"
PVTTS_VENV_NAME="${PVTTS_VENV_NAME:-venv}"
PVTTS_AUTO_SETUP="${PVTTS_AUTO_SETUP:-1}"

# 환경 설정 마커 파일
SETUP_MARKER=".pvtts_setup_done"

# ============================================================================
# 메시지 출력 함수
# ============================================================================
msg_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

msg_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

msg_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

msg_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

msg_step() {
    echo -e "${MAGENTA}[STEP]${NC} $1"
}

# ============================================================================
# 진행 스피너
# ============================================================================
spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='|/-\'
    while [ "$(ps a | awk '{print $1}' | grep $pid)" ]; do
        local temp=${spinstr#?}
        printf " [%c]  " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

# ============================================================================
# 시그널 트랩
# ============================================================================
cleanup() {
    echo ""
    msg_info "프로그램을 종료합니다..."
    exit 0
}

trap cleanup SIGINT SIGTERM

# ============================================================================
# 배너 출력
# ============================================================================
show_banner() {
    echo ""
    echo -e "${CYAN}  ____                                 _  __     __    _           ${NC}"
    echo -e "${CYAN} |  _ \\ ___ _ __ ___  ___  _ __   __ _| | \\ \\   / /__ (_) ___ ___  ${NC}"
    echo -e "${CYAN} | |_) / _ \\ '__/ __|/ _ \\| '_ \\ / _\` | |  \\ \\ / / _ \\| |/ __/ _ \\ ${NC}"
    echo -e "${CYAN} |  __/  __/ |  \\__ \\ (_) | | | | (_| | |   \\ V / (_) | | (_|  __/ ${NC}"
    echo -e "${CYAN} |_|   \\___|_|  |___/\\___/|_| |_|\\__,_|_|    \\_/ \\___/|_|\\___\\___| ${NC}"
    echo -e "${CYAN}                                                                   ${NC}"
    echo -e "${MAGENTA}              _____ _____ ____       _    ___                       ${NC}"
    echo -e "${MAGENTA}             |_   _|_   _/ ___|     / \\  |_ _|                      ${NC}"
    echo -e "${MAGENTA}               | |   | | \\___ \\    / _ \\  | |                       ${NC}"
    echo -e "${MAGENTA}               | |   | |  ___) |  / ___ \\ | |                       ${NC}"
    echo -e "${MAGENTA}               |_|   |_| |____/  /_/   \\_\\___|                      ${NC}"
    echo ""
    echo -e "${YELLOW}  Personal Voice TTS AI v1.0.0${NC}"
    echo -e "${BLUE}  음성 콜라주 및 합성 기반의 고급 TTS 시스템${NC}"
    echo ""
    echo -e "${GREEN}============================================================================${NC}"
}

# ============================================================================
# Python 확인
# ============================================================================
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON=python3
    elif command -v python &> /dev/null; then
        PYTHON=python
    else
        msg_error "Python이 설치되어 있지 않습니다."
        msg_info "https://www.python.org/downloads/ 에서 Python 3.9 이상을 설치하세요."
        exit 1
    fi

    # Python 버전 확인
    PYTHON_VERSION=$($PYTHON -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PYTHON_MAJOR=$($PYTHON -c 'import sys; print(sys.version_info.major)')
    PYTHON_MINOR=$($PYTHON -c 'import sys; print(sys.version_info.minor)')

    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]); then
        msg_error "Python 3.9 이상이 필요합니다. 현재 버전: $PYTHON_VERSION"
        exit 1
    fi

    msg_info "Python $PYTHON_VERSION 감지됨"
}

# ============================================================================
# 가상환경 존재 여부 확인
# ============================================================================
venv_exists() {
    if [ -d "$PVTTS_VENV_NAME" ] && [ -f "$PVTTS_VENV_NAME/bin/activate" ]; then
        return 0
    elif [ -d ".venv" ] && [ -f ".venv/bin/activate" ]; then
        PVTTS_VENV_NAME=".venv"
        return 0
    fi
    return 1
}

# ============================================================================
# 가상환경 생성
# ============================================================================
create_venv() {
    msg_step "가상환경 생성 중... ($PVTTS_VENV_NAME)"

    # venv 모듈 확인
    if ! $PYTHON -c "import venv" &> /dev/null; then
        msg_error "Python venv 모듈이 설치되어 있지 않습니다."
        msg_info "Ubuntu/Debian: sudo apt install python3-venv"
        msg_info "CentOS/RHEL: sudo yum install python3-venv"
        exit 1
    fi

    $PYTHON -m venv "$PVTTS_VENV_NAME"

    if [ $? -eq 0 ]; then
        msg_success "가상환경 생성 완료: $PVTTS_VENV_NAME"
    else
        msg_error "가상환경 생성 실패"
        exit 1
    fi
}

# ============================================================================
# 가상환경 활성화
# ============================================================================
activate_venv() {
    if venv_exists; then
        msg_info "가상환경 활성화 중... ($PVTTS_VENV_NAME)"
        source "$PVTTS_VENV_NAME/bin/activate"

        # 활성화된 Python 경로 업데이트
        PYTHON="$PVTTS_VENV_NAME/bin/python"
        msg_success "가상환경 활성화 완료"
    else
        msg_warn "가상환경이 감지되지 않았습니다."
        return 1
    fi
}

# ============================================================================
# pip 업그레이드
# ============================================================================
upgrade_pip() {
    msg_step "pip 업그레이드 중..."
    $PYTHON -m pip install --upgrade pip --quiet
    msg_success "pip 업그레이드 완료"
}

# ============================================================================
# 기본 의존성 설치 여부 확인
# ============================================================================
check_basic_deps() {
    # 핵심 패키지 확인 (numpy, librosa, fastapi)
    if $PYTHON -c "import numpy; import librosa; import fastapi" &> /dev/null; then
        return 0
    fi
    return 1
}

# ============================================================================
# 의존성 설치 (기본)
# ============================================================================
install_basic_deps() {
    msg_step "기본 의존성 설치 중..."

    if [ -f "requirements.txt" ]; then
        $PYTHON -m pip install -r requirements.txt --quiet
        msg_success "기본 의존성 설치 완료"
    else
        msg_error "requirements.txt 파일을 찾을 수 없습니다."
        exit 1
    fi
}

# ============================================================================
# 선택적 의존성 설치
# ============================================================================
install_optional_deps() {
    local dep_type=$1
    local req_file="requirements-${dep_type}.txt"

    if [ -f "$req_file" ]; then
        msg_step "${dep_type} 의존성 설치 중..."
        $PYTHON -m pip install -r "$req_file" --quiet
        msg_success "${dep_type} 의존성 설치 완료"
    else
        msg_warn "$req_file 파일을 찾을 수 없습니다."
    fi
}

# ============================================================================
# 자동 환경 설정 (첫 실행 시)
# ============================================================================
auto_setup() {
    local need_setup=0

    # 마커 파일이 없으면 설정 필요
    if [ ! -f "$SETUP_MARKER" ]; then
        need_setup=1
    fi

    # 가상환경이 없으면 설정 필요
    if ! venv_exists; then
        need_setup=1
    fi

    if [ $need_setup -eq 1 ]; then
        echo ""
        echo -e "${YELLOW}============================================================================${NC}"
        echo -e "${YELLOW}  첫 실행 감지 - 환경 자동 설정을 시작합니다${NC}"
        echo -e "${YELLOW}============================================================================${NC}"
        echo ""

        # 가상환경 생성
        if ! venv_exists; then
            create_venv
        fi

        # 가상환경 활성화
        activate_venv

        # pip 업그레이드
        upgrade_pip

        # 기본 의존성 설치
        if ! check_basic_deps; then
            install_basic_deps
        fi

        # 마커 파일 생성
        echo "setup_date=$(date '+%Y-%m-%d %H:%M:%S')" > "$SETUP_MARKER"
        echo "python_version=$PYTHON_VERSION" >> "$SETUP_MARKER"
        echo "venv_name=$PVTTS_VENV_NAME" >> "$SETUP_MARKER"

        echo ""
        echo -e "${GREEN}============================================================================${NC}"
        echo -e "${GREEN}  환경 설정 완료!${NC}"
        echo -e "${GREEN}============================================================================${NC}"
        echo ""

        return 0
    fi

    return 1
}

# ============================================================================
# 환경 확인 및 준비 (메인 진입점)
# ============================================================================
ensure_environment() {
    check_python

    # 자동 설정이 활성화된 경우
    if [ "$PVTTS_AUTO_SETUP" = "1" ]; then
        auto_setup
    fi

    # 가상환경 활성화 시도
    if venv_exists; then
        activate_venv
    else
        msg_warn "가상환경이 없습니다. 시스템 Python을 사용합니다."
        msg_info "가상환경 생성: ./run.sh setup"
    fi

    # 의존성 확인
    if ! check_basic_deps; then
        msg_warn "필수 의존성이 설치되어 있지 않습니다."
        msg_info "의존성 설치: ./run.sh install basic"

        if [ "$PVTTS_AUTO_SETUP" = "1" ]; then
            echo ""
            read -p "  지금 기본 의존성을 설치하시겠습니까? (Y/n): " install_choice
            if [ "$install_choice" != "n" ] && [ "$install_choice" != "N" ]; then
                install_basic_deps
            fi
        fi
    fi
}

# ============================================================================
# 전체 환경 설정 (수동)
# ============================================================================
run_setup() {
    shift || true

    echo ""
    echo -e "${BOLD}${CYAN}  환경 설정 옵션:${NC}"
    echo ""
    echo -e "  ${GREEN}[1]${NC} 기본 설정        - 가상환경 + 필수 의존성"
    echo -e "  ${GREEN}[2]${NC} GUI 포함 설정    - 기본 + PyQt6 GUI"
    echo -e "  ${GREEN}[3]${NC} TTS 포함 설정    - 기본 + TTS 백엔드"
    echo -e "  ${GREEN}[4]${NC} 전체 설정        - 모든 의존성 설치"
    echo -e "  ${GREEN}[5]${NC} 개발 환경 설정   - 전체 + 개발 도구"
    echo -e "  ${GREEN}[0]${NC} 취소"
    echo ""
    read -p "  선택 (0-5): " setup_choice

    case $setup_choice in
        1) setup_basic ;;
        2) setup_with_gui ;;
        3) setup_with_tts ;;
        4) setup_full ;;
        5) setup_dev ;;
        0) return ;;
        *)
            msg_error "잘못된 선택입니다."
            run_setup ""
            ;;
    esac
}

setup_basic() {
    msg_info "기본 환경 설정 시작..."

    check_python

    if ! venv_exists; then
        create_venv
    fi

    activate_venv
    upgrade_pip
    install_basic_deps

    # 마커 파일 업데이트
    echo "setup_date=$(date '+%Y-%m-%d %H:%M:%S')" > "$SETUP_MARKER"
    echo "setup_type=basic" >> "$SETUP_MARKER"

    msg_success "기본 환경 설정 완료!"
}

setup_with_gui() {
    setup_basic
    install_optional_deps "gui"

    echo "setup_type=gui" >> "$SETUP_MARKER"
    msg_success "GUI 포함 환경 설정 완료!"
}

setup_with_tts() {
    setup_basic
    install_optional_deps "tts"

    echo "setup_type=tts" >> "$SETUP_MARKER"
    msg_success "TTS 포함 환경 설정 완료!"
}

setup_full() {
    setup_basic
    install_optional_deps "gui"
    install_optional_deps "tts"
    install_optional_deps "ai"

    echo "setup_type=full" >> "$SETUP_MARKER"
    msg_success "전체 환경 설정 완료!"
}

setup_dev() {
    setup_full
    install_optional_deps "dev"

    echo "setup_type=dev" >> "$SETUP_MARKER"
    msg_success "개발 환경 설정 완료!"
}

# ============================================================================
# 환경 상태 표시
# ============================================================================
show_status() {
    echo ""
    echo -e "${BOLD}${CYAN}  환경 상태:${NC}"
    echo ""

    # Python
    if command -v python3 &> /dev/null || command -v python &> /dev/null; then
        local py_ver=$($PYTHON -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")')
        echo -e "  Python:        ${GREEN}$py_ver${NC}"
    else
        echo -e "  Python:        ${RED}미설치${NC}"
    fi

    # 가상환경
    if venv_exists; then
        echo -e "  가상환경:      ${GREEN}$PVTTS_VENV_NAME${NC}"
    else
        echo -e "  가상환경:      ${YELLOW}없음${NC}"
    fi

    # 설정 마커
    if [ -f "$SETUP_MARKER" ]; then
        local setup_date=$(grep "setup_date" "$SETUP_MARKER" | cut -d'=' -f2)
        local setup_type=$(grep "setup_type" "$SETUP_MARKER" | cut -d'=' -f2)
        echo -e "  설정 일시:     ${GREEN}$setup_date${NC}"
        echo -e "  설정 유형:     ${GREEN}${setup_type:-basic}${NC}"
    else
        echo -e "  설정 상태:     ${YELLOW}미설정${NC}"
    fi

    # 의존성 상태
    echo ""
    echo -e "  ${BOLD}의존성 상태:${NC}"

    # 기본 의존성
    if $PYTHON -c "import numpy" &> /dev/null; then
        echo -e "    numpy:       ${GREEN}설치됨${NC}"
    else
        echo -e "    numpy:       ${RED}미설치${NC}"
    fi

    if $PYTHON -c "import librosa" &> /dev/null; then
        echo -e "    librosa:     ${GREEN}설치됨${NC}"
    else
        echo -e "    librosa:     ${RED}미설치${NC}"
    fi

    if $PYTHON -c "import fastapi" &> /dev/null; then
        echo -e "    fastapi:     ${GREEN}설치됨${NC}"
    else
        echo -e "    fastapi:     ${RED}미설치${NC}"
    fi

    # GUI
    if $PYTHON -c "import PyQt6" &> /dev/null; then
        echo -e "    PyQt6:       ${GREEN}설치됨${NC}"
    else
        echo -e "    PyQt6:       ${YELLOW}미설치${NC}"
    fi

    # TTS
    if $PYTHON -c "import gtts" &> /dev/null; then
        echo -e "    gTTS:        ${GREEN}설치됨${NC}"
    else
        echo -e "    gTTS:        ${YELLOW}미설치${NC}"
    fi

    if $PYTHON -c "import edge_tts" &> /dev/null; then
        echo -e "    edge-tts:    ${GREEN}설치됨${NC}"
    else
        echo -e "    edge-tts:    ${YELLOW}미설치${NC}"
    fi

    echo ""
}

# ============================================================================
# 웹 서버 실행
# ============================================================================
run_web() {
    shift || true
    local host="$PVTTS_HOST"
    local port="$PVTTS_PORT"

    while [[ $# -gt 0 ]]; do
        case $1 in
            --host)
                host="$2"
                shift 2
                ;;
            --port|-p)
                port="$2"
                shift 2
                ;;
            *)
                shift
                ;;
        esac
    done

    echo ""
    msg_info "웹 서버 시작 중..."
    msg_info "호스트: $host"
    msg_info "포트: $port"
    echo ""
    msg_success "브라우저에서 http://localhost:$port 로 접속하세요"
    echo ""

    if [ "$PVTTS_DEBUG" = "1" ]; then
        $PYTHON -m uvicorn web.app:app --host "$host" --port "$port" --reload --log-level debug
    else
        $PYTHON -m uvicorn web.app:app --host "$host" --port "$port" --reload
    fi
}

# ============================================================================
# GUI 실행
# ============================================================================
run_gui() {
    echo ""
    msg_info "GUI 애플리케이션 시작 중..."

    # PyQt6 확인
    if ! $PYTHON -c "import PyQt6" &> /dev/null; then
        msg_error "PyQt6가 설치되어 있지 않습니다."
        msg_info "설치 명령: ./run.sh install gui"

        read -p "  지금 GUI 의존성을 설치하시겠습니까? (Y/n): " install_choice
        if [ "$install_choice" != "n" ] && [ "$install_choice" != "N" ]; then
            install_optional_deps "gui"
        else
            return 1
        fi
    fi

    $PYTHON -m gui.app
}

# ============================================================================
# CLI 도구 실행
# ============================================================================
run_cli() {
    shift || true
    if [ $# -eq 0 ]; then
        cli_menu
    else
        $PYTHON -m cli."$@"
    fi
}

cli_menu() {
    echo ""
    echo -e "${BOLD}${CYAN}  CLI 도구 선택:${NC}"
    echo ""
    echo -e "  ${GREEN}[1]${NC} basic      - 기본 오디오 처리 (info, spectrogram, waveform)"
    echo -e "  ${GREEN}[2]${NC} similarity - 유사도 검출 (find, compare, batch)"
    echo -e "  ${GREEN}[3]${NC} synthesize - 오디오 합성 (collage, blend)"
    echo -e "  ${GREEN}[4]${NC} tts        - TTS 변환 (speak, collage, batch)"
    echo -e "  ${GREEN}[5]${NC} batch      - 배치 처리 (run, list-workflows, monitor)"
    echo -e "  ${GREEN}[0]${NC} 뒤로 가기"
    echo ""
    read -p "  선택 (0-5): " cli_choice

    case $cli_choice in
        1)
            msg_info "CLI basic 도움말:"
            $PYTHON -m cli.basic --help
            cli_menu
            ;;
        2)
            msg_info "CLI similarity 도움말:"
            $PYTHON -m cli.similarity --help
            cli_menu
            ;;
        3)
            msg_info "CLI synthesize 도움말:"
            $PYTHON -m cli.synthesize --help
            cli_menu
            ;;
        4)
            msg_info "CLI tts 도움말:"
            $PYTHON -m cli.tts --help
            cli_menu
            ;;
        5)
            msg_info "CLI batch 도움말:"
            $PYTHON -m cli.batch --help
            cli_menu
            ;;
        0)
            interactive_menu
            ;;
        *)
            msg_error "잘못된 선택입니다."
            cli_menu
            ;;
    esac
}

# ============================================================================
# 테스트 실행
# ============================================================================
run_test() {
    shift || true

    # pytest 확인
    if ! $PYTHON -c "import pytest" &> /dev/null; then
        msg_error "pytest가 설치되어 있지 않습니다."
        msg_info "설치 명령: ./run.sh install dev"

        read -p "  지금 개발 의존성을 설치하시겠습니까? (Y/n): " install_choice
        if [ "$install_choice" != "n" ] && [ "$install_choice" != "N" ]; then
            install_optional_deps "dev"
        else
            return 1
        fi
    fi

    case $1 in
        --verbose|-v)
            msg_info "상세 테스트 실행 중..."
            $PYTHON -m pytest tests/ -v --tb=short
            ;;
        --quiet|-q)
            msg_info "간략 테스트 실행 중..."
            $PYTHON -m pytest tests/ -q
            ;;
        --coverage|-c)
            msg_info "커버리지 테스트 실행 중..."
            $PYTHON -m pytest tests/ --cov=core --cov=algorithms --cov=web --cov=gui --cov-report=html --cov-report=term
            msg_success "HTML 커버리지 리포트: htmlcov/index.html"
            ;;
        "")
            test_menu
            ;;
        *)
            msg_info "테스트 실행 중..."
            $PYTHON -m pytest tests/ --tb=short
            ;;
    esac
}

test_menu() {
    echo ""
    echo -e "${BOLD}${CYAN}  테스트 옵션:${NC}"
    echo ""
    echo -e "  ${GREEN}[1]${NC} 기본 테스트       - pytest 기본 실행"
    echo -e "  ${GREEN}[2]${NC} 상세 테스트       - pytest -v (상세 출력)"
    echo -e "  ${GREEN}[3]${NC} 간략 테스트       - pytest -q (간략 출력)"
    echo -e "  ${GREEN}[4]${NC} 커버리지 테스트   - pytest --cov (커버리지 포함)"
    echo -e "  ${GREEN}[0]${NC} 뒤로 가기"
    echo ""
    read -p "  선택 (0-4): " test_choice

    case $test_choice in
        1)
            msg_info "테스트 실행 중..."
            $PYTHON -m pytest tests/ --tb=short
            ;;
        2)
            msg_info "상세 테스트 실행 중..."
            $PYTHON -m pytest tests/ -v --tb=short
            ;;
        3)
            msg_info "간략 테스트 실행 중..."
            $PYTHON -m pytest tests/ -q
            ;;
        4)
            msg_info "커버리지 테스트 실행 중..."
            $PYTHON -m pytest tests/ --cov=core --cov=algorithms --cov=web --cov=gui --cov-report=html --cov-report=term
            msg_success "HTML 커버리지 리포트: htmlcov/index.html"
            ;;
        0)
            interactive_menu
            ;;
        *)
            msg_error "잘못된 선택입니다."
            test_menu
            ;;
    esac
}

# ============================================================================
# 의존성 설치
# ============================================================================
install_deps() {
    shift || true
    case $1 in
        basic)
            install_basic
            ;;
        ai)
            install_ai
            ;;
        gui)
            install_gui
            ;;
        tts)
            install_tts
            ;;
        dev)
            install_dev
            ;;
        all)
            install_all
            ;;
        "")
            install_menu
            ;;
        *)
            install_basic
            ;;
    esac
}

install_menu() {
    echo ""
    echo -e "${BOLD}${CYAN}  설치 옵션:${NC}"
    echo ""
    echo -e "  ${GREEN}[1]${NC} 기본 패키지       - 필수 의존성만 설치"
    echo -e "  ${GREEN}[2]${NC} AI 패키지         - Wav2Vec2, HuBERT 등 AI 모델"
    echo -e "  ${GREEN}[3]${NC} GUI 패키지        - PyQt6 GUI 의존성"
    echo -e "  ${GREEN}[4]${NC} TTS 패키지        - gTTS, Edge-TTS 등"
    echo -e "  ${GREEN}[5]${NC} 개발 패키지       - pytest, black, flake8 등"
    echo -e "  ${GREEN}[6]${NC} 전체 패키지       - 모든 의존성 설치"
    echo -e "  ${GREEN}[0]${NC} 뒤로 가기"
    echo ""
    read -p "  선택 (0-6): " install_choice

    case $install_choice in
        1) install_basic ;;
        2) install_ai ;;
        3) install_gui ;;
        4) install_tts ;;
        5) install_dev ;;
        6) install_all ;;
        0) interactive_menu ;;
        *)
            msg_error "잘못된 선택입니다."
            install_menu
            ;;
    esac
}

install_basic() {
    msg_info "기본 의존성 설치 중..."
    $PYTHON -m pip install --upgrade pip
    $PYTHON -m pip install -r requirements.txt
    msg_success "기본 의존성 설치 완료!"
}

install_ai() {
    msg_info "AI 의존성 설치 중..."
    $PYTHON -m pip install --upgrade pip
    if [ -f "requirements-ai.txt" ]; then
        $PYTHON -m pip install -r requirements-ai.txt
    else
        $PYTHON -m pip install ".[ai]"
    fi
    msg_success "AI 의존성 설치 완료!"
}

install_gui() {
    msg_info "GUI 의존성 설치 중..."
    $PYTHON -m pip install --upgrade pip
    if [ -f "requirements-gui.txt" ]; then
        $PYTHON -m pip install -r requirements-gui.txt
    else
        $PYTHON -m pip install ".[gui]"
    fi
    msg_success "GUI 의존성 설치 완료!"
}

install_tts() {
    msg_info "TTS 의존성 설치 중..."
    $PYTHON -m pip install --upgrade pip
    if [ -f "requirements-tts.txt" ]; then
        $PYTHON -m pip install -r requirements-tts.txt
    else
        $PYTHON -m pip install ".[tts]"
    fi
    msg_success "TTS 의존성 설치 완료!"
}

install_dev() {
    msg_info "개발 의존성 설치 중..."
    $PYTHON -m pip install --upgrade pip
    if [ -f "requirements-dev.txt" ]; then
        $PYTHON -m pip install -r requirements-dev.txt
    else
        $PYTHON -m pip install ".[dev]"
    fi
    msg_success "개발 의존성 설치 완료!"
}

install_all() {
    msg_info "전체 의존성 설치 중..."
    $PYTHON -m pip install --upgrade pip
    $PYTHON -m pip install -r requirements.txt
    [ -f "requirements-ai.txt" ] && $PYTHON -m pip install -r requirements-ai.txt
    [ -f "requirements-gui.txt" ] && $PYTHON -m pip install -r requirements-gui.txt
    [ -f "requirements-tts.txt" ] && $PYTHON -m pip install -r requirements-tts.txt
    [ -f "requirements-dev.txt" ] && $PYTHON -m pip install -r requirements-dev.txt
    msg_success "전체 의존성 설치 완료!"
}

# ============================================================================
# 프로젝트 정리
# ============================================================================
clean_project() {
    echo ""
    msg_info "프로젝트 정리 중..."

    # Python 캐시 삭제
    msg_info "__pycache__ 디렉토리 삭제 중..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

    # .pyc 파일 삭제
    msg_info ".pyc 파일 삭제 중..."
    find . -type f -name "*.pyc" -delete 2>/dev/null || true

    # pytest 캐시 삭제
    msg_info ".pytest_cache 디렉토리 삭제 중..."
    rm -rf .pytest_cache 2>/dev/null || true

    # mypy 캐시 삭제
    msg_info ".mypy_cache 디렉토리 삭제 중..."
    rm -rf .mypy_cache 2>/dev/null || true

    # 빌드 디렉토리 삭제
    msg_info "빌드 디렉토리 삭제 중..."
    rm -rf build dist *.egg-info 2>/dev/null || true

    # 커버리지 파일 삭제
    msg_info "커버리지 파일 삭제 중..."
    rm -f .coverage 2>/dev/null || true
    rm -rf htmlcov 2>/dev/null || true

    msg_success "프로젝트 정리 완료!"
}

# ============================================================================
# 환경 초기화 (가상환경 삭제)
# ============================================================================
reset_environment() {
    echo ""
    msg_warn "이 작업은 가상환경과 설정을 모두 삭제합니다."
    read -p "  계속하시겠습니까? (y/N): " reset_choice

    if [ "$reset_choice" = "y" ] || [ "$reset_choice" = "Y" ]; then
        msg_info "환경 초기화 중..."

        # 가상환경 삭제
        if [ -d "$PVTTS_VENV_NAME" ]; then
            rm -rf "$PVTTS_VENV_NAME"
            msg_info "가상환경 삭제됨: $PVTTS_VENV_NAME"
        fi

        if [ -d ".venv" ]; then
            rm -rf ".venv"
            msg_info "가상환경 삭제됨: .venv"
        fi

        # 마커 파일 삭제
        if [ -f "$SETUP_MARKER" ]; then
            rm -f "$SETUP_MARKER"
            msg_info "설정 마커 삭제됨"
        fi

        clean_project

        msg_success "환경 초기화 완료!"
        msg_info "다시 실행하면 환경이 자동으로 설정됩니다."
    else
        msg_info "취소되었습니다."
    fi
}

# ============================================================================
# 도움말 출력
# ============================================================================
show_help() {
    echo ""
    echo -e "${BOLD}${CYAN}Personal Voice TTS AI - 사용법${NC}"
    echo ""
    echo -e "${YELLOW}사용법:${NC}"
    echo "  ./run.sh [명령어] [옵션]"
    echo ""
    echo -e "${YELLOW}명령어:${NC}"
    echo -e "  ${GREEN}web${NC}      웹 서버 실행 (기본값)"
    echo "           옵션: --host <호스트>, --port/-p <포트>"
    echo -e "  ${GREEN}gui${NC}      GUI 애플리케이션 실행"
    echo -e "  ${GREEN}cli${NC}      CLI 도구 실행"
    echo "           서브명령: basic, similarity, synthesize, tts, batch"
    echo -e "  ${GREEN}test${NC}     테스트 실행"
    echo "           옵션: -v (상세), -q (간략), -c (커버리지)"
    echo -e "  ${GREEN}install${NC}  의존성 설치"
    echo "           옵션: basic, ai, gui, tts, dev, all"
    echo -e "  ${GREEN}setup${NC}    환경 설정 (가상환경 생성 + 의존성 설치)"
    echo -e "  ${GREEN}status${NC}   환경 상태 표시"
    echo -e "  ${GREEN}reset${NC}    환경 초기화 (가상환경 삭제)"
    echo -e "  ${GREEN}clean${NC}    캐시 및 빌드 파일 정리"
    echo -e "  ${GREEN}menu${NC}     대화형 메뉴 표시"
    echo -e "  ${GREEN}help${NC}     도움말 표시"
    echo ""
    echo -e "${YELLOW}환경변수:${NC}"
    echo -e "  ${CYAN}PVTTS_HOST${NC}       웹 서버 호스트 (기본값: 0.0.0.0)"
    echo -e "  ${CYAN}PVTTS_PORT${NC}       웹 서버 포트 (기본값: 8000)"
    echo -e "  ${CYAN}PVTTS_DEBUG${NC}      디버그 모드 (1로 설정하면 활성화)"
    echo -e "  ${CYAN}PVTTS_VENV_NAME${NC}  가상환경 디렉토리 이름 (기본값: venv)"
    echo -e "  ${CYAN}PVTTS_AUTO_SETUP${NC} 자동 환경 설정 (기본값: 1, 0으로 비활성화)"
    echo ""
    echo -e "${YELLOW}예시:${NC}"
    echo "  ./run.sh                           # 대화형 메뉴 (첫 실행 시 자동 설정)"
    echo "  ./run.sh setup                     # 환경 수동 설정"
    echo "  ./run.sh web                       # 웹 서버 실행 (기본 포트)"
    echo "  ./run.sh web --port 3000           # 웹 서버 (포트 3000)"
    echo "  ./run.sh gui                       # GUI 실행"
    echo "  ./run.sh cli basic info audio.wav  # CLI 오디오 정보"
    echo "  ./run.sh test -v                   # 상세 테스트"
    echo "  ./run.sh install all               # 전체 의존성 설치"
    echo "  ./run.sh status                    # 환경 상태 확인"
    echo "  ./run.sh reset                     # 환경 초기화"
    echo "  ./run.sh clean                     # 캐시 정리"
    echo ""
    echo "  PVTTS_AUTO_SETUP=0 ./run.sh web    # 자동 설정 비활성화"
    echo ""
}

# ============================================================================
# 대화형 메뉴
# ============================================================================
interactive_menu() {
    echo ""
    echo -e "${BOLD}${CYAN}  메뉴를 선택하세요:${NC}"
    echo ""
    echo -e "  ${GREEN}[1]${NC} 웹 서버 실행         - FastAPI 웹 서비스 시작"
    echo -e "  ${GREEN}[2]${NC} GUI 실행             - PyQt6 GUI 애플리케이션 시작"
    echo -e "  ${GREEN}[3]${NC} CLI 도구             - CLI 명령어 도움말"
    echo -e "  ${GREEN}[4]${NC} 테스트 실행          - pytest 테스트 스위트 실행"
    echo -e "  ${GREEN}[5]${NC} 의존성 설치          - pip 패키지 설치"
    echo -e "  ${GREEN}[6]${NC} 환경 설정            - 가상환경 + 의존성 설정"
    echo -e "  ${GREEN}[7]${NC} 환경 상태            - 현재 환경 정보 표시"
    echo -e "  ${GREEN}[8]${NC} 정리                 - 캐시 및 빌드 파일 삭제"
    echo -e "  ${GREEN}[9]${NC} 도움말               - 상세 사용법 표시"
    echo -e "  ${GREEN}[0]${NC} 종료"
    echo ""
    read -p "  선택 (0-9): " menu_choice

    case $menu_choice in
        1) run_web "" ;;
        2) run_gui ;;
        3) cli_menu ;;
        4) test_menu ;;
        5) install_menu ;;
        6) run_setup "" ;;
        7) show_status ;;
        8) clean_project ;;
        9) show_help ;;
        0)
            echo ""
            msg_info "프로그램을 종료합니다."
            exit 0
            ;;
        *)
            msg_error "잘못된 선택입니다. 0-9 사이의 숫자를 입력하세요."
            interactive_menu
            ;;
    esac
}

# ============================================================================
# 메인 실행
# ============================================================================
main() {
    show_banner

    COMMAND=${1:-menu}

    # Python 불필요한 명령어 먼저 처리
    case $COMMAND in
        help|--help|-h)
            show_help
            exit 0
            ;;
        clean)
            clean_project
            exit 0
            ;;
        reset)
            check_python
            reset_environment
            exit 0
            ;;
    esac

    # Python 필요한 명령어 - 환경 확인 및 준비
    ensure_environment

    case $COMMAND in
        web)
            run_web "$@"
            ;;
        gui)
            run_gui
            ;;
        cli)
            run_cli "$@"
            ;;
        test)
            run_test "$@"
            ;;
        install)
            install_deps "$@"
            ;;
        setup)
            run_setup "$@"
            ;;
        status)
            show_status
            ;;
        menu)
            interactive_menu
            ;;
        *)
            msg_error "알 수 없는 명령어: $COMMAND"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
