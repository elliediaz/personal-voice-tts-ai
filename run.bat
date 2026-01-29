@echo off
REM ============================================================================
REM Personal Voice TTS AI - 향상된 실행 스크립트 (Windows)
REM 버전: 0.9.0
REM ============================================================================
REM
REM 사용법: run.bat [명령어] [옵션]
REM
REM 명령어:
REM   web      - 웹 서버 실행 (기본값)
REM   gui      - GUI 애플리케이션 실행
REM   cli      - CLI 도구 실행
REM   test     - 테스트 실행
REM   install  - 의존성 설치
REM   clean    - 캐시 및 빌드 파일 정리
REM   help     - 도움말 표시
REM
REM 환경변수:
REM   PVTTS_HOST   - 웹 서버 호스트 (기본값: 0.0.0.0)
REM   PVTTS_PORT   - 웹 서버 포트 (기본값: 8000)
REM   PVTTS_DEBUG  - 디버그 모드 (1로 설정하면 활성화)
REM ============================================================================

setlocal enabledelayedexpansion

REM 프로젝트 디렉토리로 이동
cd /d "%~dp0"

REM ============================================================================
REM 색상 코드 정의 (ANSI 이스케이프 시퀀스)
REM ============================================================================
REM Windows 10 이상에서 ANSI 지원
for /F %%a in ('echo prompt $E ^| cmd') do set "ESC=%%a"
set "GREEN=%ESC%[92m"
set "RED=%ESC%[91m"
set "YELLOW=%ESC%[93m"
set "BLUE=%ESC%[94m"
set "CYAN=%ESC%[96m"
set "MAGENTA=%ESC%[95m"
set "RESET=%ESC%[0m"
set "BOLD=%ESC%[1m"

REM ============================================================================
REM 환경 변수 기본값 설정
REM ============================================================================
if "%PVTTS_HOST%"=="" set PVTTS_HOST=0.0.0.0
if "%PVTTS_PORT%"=="" set PVTTS_PORT=8000
if "%PVTTS_DEBUG%"=="" set PVTTS_DEBUG=0

REM ============================================================================
REM 배너 출력
REM ============================================================================
:show_banner
echo.
echo %CYAN%  ____                                 _  __     __    _           %RESET%
echo %CYAN% ^|  _ \ ___ _ __ ___  ___  _ __   __ _^| ^| \ \   / /__ (_) ___ ___  %RESET%
echo %CYAN% ^| ^|_) / _ \ '__/ __^|/ _ \^| '_ \ / _` ^| ^|  \ \ / / _ \^| ^|/ __/ _ \ %RESET%
echo %CYAN% ^|  __/  __/ ^|  \__ \ (_) ^| ^| ^| ^| (_^| ^| ^|   \ V / (_) ^| ^| (_^|  __/ %RESET%
echo %CYAN% ^|_^|   \___ ^|_^|  ^|___/\___/^|_^| ^|_^|\__,_^|_^|    \_/ \___/^|_^|\___\___^| %RESET%
echo %CYAN%                                                                   %RESET%
echo %MAGENTA%              _____ _____ ____       _    ___                       %RESET%
echo %MAGENTA%             ^|_   _^|_   _/ ___^|     / \  ^|_ _^|                      %RESET%
echo %MAGENTA%               ^| ^|   ^| ^| \___ \    / _ \  ^| ^|                       %RESET%
echo %MAGENTA%               ^| ^|   ^| ^|  ___) ^|  / ___ \ ^| ^|                       %RESET%
echo %MAGENTA%               ^|_^|   ^|_^| ^|____/  /_/   \_\___ ^|                      %RESET%
echo.
echo %YELLOW%  Personal Voice TTS AI v0.9.0%RESET%
echo %BLUE%  음성 콜라주 및 합성 기반의 고급 TTS 시스템%RESET%
echo.
echo %GREEN%============================================================================%RESET%

REM ============================================================================
REM Python 확인
REM ============================================================================
:check_python
where python >nul 2>nul
if %errorlevel% neq 0 (
    call :msg_error "Python이 설치되어 있지 않습니다."
    call :msg_info "https://www.python.org/downloads/ 에서 Python 3.9 이상을 설치하세요."
    exit /b 1
)

REM Python 버전 확인
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set PYTHON_MAJOR=%%a
    set PYTHON_MINOR=%%b
)

if %PYTHON_MAJOR% lss 3 (
    call :msg_error "Python 3.9 이상이 필요합니다. 현재 버전: %PYTHON_VERSION%"
    exit /b 1
)
if %PYTHON_MAJOR% equ 3 if %PYTHON_MINOR% lss 9 (
    call :msg_error "Python 3.9 이상이 필요합니다. 현재 버전: %PYTHON_VERSION%"
    exit /b 1
)

call :msg_info "Python %PYTHON_VERSION% 감지됨"

REM ============================================================================
REM 가상환경 활성화
REM ============================================================================
:activate_venv
if exist "venv\Scripts\activate.bat" (
    call :msg_info "가상환경 활성화 중... (venv)"
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    call :msg_info "가상환경 활성화 중... (.venv)"
    call .venv\Scripts\activate.bat
) else (
    call :msg_warn "가상환경이 감지되지 않았습니다. 시스템 Python을 사용합니다."
)

REM ============================================================================
REM 명령어 처리
REM ============================================================================
set COMMAND=%1
if "%COMMAND%"=="" goto :interactive_menu

if "%COMMAND%"=="web" goto :run_web
if "%COMMAND%"=="gui" goto :run_gui
if "%COMMAND%"=="cli" goto :run_cli
if "%COMMAND%"=="test" goto :run_test
if "%COMMAND%"=="install" goto :install_deps
if "%COMMAND%"=="clean" goto :clean_project
if "%COMMAND%"=="help" goto :show_help
if "%COMMAND%"=="--help" goto :show_help
if "%COMMAND%"=="-h" goto :show_help
if "%COMMAND%"=="menu" goto :interactive_menu

call :msg_error "알 수 없는 명령어: %COMMAND%"
goto :show_help

REM ============================================================================
REM 대화형 메뉴
REM ============================================================================
:interactive_menu
echo.
echo %BOLD%%CYAN%  메뉴를 선택하세요:%RESET%
echo.
echo   %GREEN%[1]%RESET% 웹 서버 실행         - FastAPI 웹 서비스 시작
echo   %GREEN%[2]%RESET% GUI 실행             - PyQt6 GUI 애플리케이션 시작
echo   %GREEN%[3]%RESET% CLI 도구             - CLI 명령어 도움말
echo   %GREEN%[4]%RESET% 테스트 실행          - pytest 테스트 스위트 실행
echo   %GREEN%[5]%RESET% 의존성 설치          - pip 패키지 설치
echo   %GREEN%[6]%RESET% 정리                 - 캐시 및 빌드 파일 삭제
echo   %GREEN%[7]%RESET% 도움말               - 상세 사용법 표시
echo   %GREEN%[0]%RESET% 종료
echo.
set /p MENU_CHOICE="  선택 (0-7): "

if "%MENU_CHOICE%"=="1" goto :run_web
if "%MENU_CHOICE%"=="2" goto :run_gui
if "%MENU_CHOICE%"=="3" goto :cli_menu
if "%MENU_CHOICE%"=="4" goto :test_menu
if "%MENU_CHOICE%"=="5" goto :install_menu
if "%MENU_CHOICE%"=="6" goto :clean_project
if "%MENU_CHOICE%"=="7" goto :show_help
if "%MENU_CHOICE%"=="0" goto :exit_script

call :msg_error "잘못된 선택입니다. 0-7 사이의 숫자를 입력하세요."
goto :interactive_menu

REM ============================================================================
REM 웹 서버 실행
REM ============================================================================
:run_web
shift
set WEB_HOST=%PVTTS_HOST%
set WEB_PORT=%PVTTS_PORT%

:parse_web_args
if "%1"=="" goto :start_web
if "%1"=="--host" (
    set WEB_HOST=%2
    shift
    shift
    goto :parse_web_args
)
if "%1"=="--port" (
    set WEB_PORT=%2
    shift
    shift
    goto :parse_web_args
)
if "%1"=="-p" (
    set WEB_PORT=%2
    shift
    shift
    goto :parse_web_args
)
shift
goto :parse_web_args

:start_web
echo.
call :msg_info "웹 서버 시작 중..."
call :msg_info "호스트: %WEB_HOST%"
call :msg_info "포트: %WEB_PORT%"
echo.
call :msg_success "브라우저에서 http://localhost:%WEB_PORT% 로 접속하세요"
echo.
if "%PVTTS_DEBUG%"=="1" (
    python -m uvicorn web.app:app --host %WEB_HOST% --port %WEB_PORT% --reload --log-level debug
) else (
    python -m uvicorn web.app:app --host %WEB_HOST% --port %WEB_PORT% --reload
)
goto :eof

REM ============================================================================
REM GUI 실행
REM ============================================================================
:run_gui
echo.
call :msg_info "GUI 애플리케이션 시작 중..."
python -m gui.app
if %errorlevel% neq 0 (
    call :msg_error "GUI 실행 실패. PyQt6가 설치되어 있는지 확인하세요."
    call :msg_info "설치 명령: run.bat install gui"
)
goto :eof

REM ============================================================================
REM CLI 메뉴
REM ============================================================================
:run_cli
shift
if "%1"=="" goto :cli_menu

REM CLI 명령어 실행
python -m cli.%*
goto :eof

:cli_menu
echo.
echo %BOLD%%CYAN%  CLI 도구 선택:%RESET%
echo.
echo   %GREEN%[1]%RESET% basic      - 기본 오디오 처리 (info, spectrogram, waveform)
echo   %GREEN%[2]%RESET% similarity - 유사도 검출 (find, compare, batch)
echo   %GREEN%[3]%RESET% synthesize - 오디오 합성 (collage, blend)
echo   %GREEN%[4]%RESET% tts        - TTS 변환 (speak, collage, batch)
echo   %GREEN%[5]%RESET% batch      - 배치 처리 (run, list-workflows, monitor)
echo   %GREEN%[0]%RESET% 뒤로 가기
echo.
set /p CLI_CHOICE="  선택 (0-5): "

if "%CLI_CHOICE%"=="1" goto :cli_basic
if "%CLI_CHOICE%"=="2" goto :cli_similarity
if "%CLI_CHOICE%"=="3" goto :cli_synthesize
if "%CLI_CHOICE%"=="4" goto :cli_tts
if "%CLI_CHOICE%"=="5" goto :cli_batch
if "%CLI_CHOICE%"=="0" goto :interactive_menu

call :msg_error "잘못된 선택입니다."
goto :cli_menu

:cli_basic
call :msg_info "CLI basic 도움말:"
python -m cli.basic --help
goto :cli_menu

:cli_similarity
call :msg_info "CLI similarity 도움말:"
python -m cli.similarity --help
goto :cli_menu

:cli_synthesize
call :msg_info "CLI synthesize 도움말:"
python -m cli.synthesize --help
goto :cli_menu

:cli_tts
call :msg_info "CLI tts 도움말:"
python -m cli.tts --help
goto :cli_menu

:cli_batch
call :msg_info "CLI batch 도움말:"
python -m cli.batch --help
goto :cli_menu

REM ============================================================================
REM 테스트 메뉴
REM ============================================================================
:run_test
shift
if "%1"=="--verbose" goto :test_verbose
if "%1"=="-v" goto :test_verbose
if "%1"=="--quiet" goto :test_quiet
if "%1"=="-q" goto :test_quiet
if "%1"=="--coverage" goto :test_coverage
if "%1"=="-c" goto :test_coverage
if "%1"=="" goto :test_menu
goto :test_default

:test_menu
echo.
echo %BOLD%%CYAN%  테스트 옵션:%RESET%
echo.
echo   %GREEN%[1]%RESET% 기본 테스트       - pytest 기본 실행
echo   %GREEN%[2]%RESET% 상세 테스트       - pytest -v (상세 출력)
echo   %GREEN%[3]%RESET% 간략 테스트       - pytest -q (간략 출력)
echo   %GREEN%[4]%RESET% 커버리지 테스트   - pytest --cov (커버리지 포함)
echo   %GREEN%[0]%RESET% 뒤로 가기
echo.
set /p TEST_CHOICE="  선택 (0-4): "

if "%TEST_CHOICE%"=="1" goto :test_default
if "%TEST_CHOICE%"=="2" goto :test_verbose
if "%TEST_CHOICE%"=="3" goto :test_quiet
if "%TEST_CHOICE%"=="4" goto :test_coverage
if "%TEST_CHOICE%"=="0" goto :interactive_menu

call :msg_error "잘못된 선택입니다."
goto :test_menu

:test_default
call :msg_info "테스트 실행 중..."
python -m pytest tests/ --tb=short
goto :eof

:test_verbose
call :msg_info "상세 테스트 실행 중..."
python -m pytest tests/ -v --tb=short
goto :eof

:test_quiet
call :msg_info "간략 테스트 실행 중..."
python -m pytest tests/ -q
goto :eof

:test_coverage
call :msg_info "커버리지 테스트 실행 중..."
python -m pytest tests/ --cov=core --cov=algorithms --cov=web --cov=gui --cov-report=html --cov-report=term
call :msg_success "HTML 커버리지 리포트: htmlcov/index.html"
goto :eof

REM ============================================================================
REM 의존성 설치 메뉴
REM ============================================================================
:install_deps
shift
if "%1"=="basic" goto :install_basic
if "%1"=="ai" goto :install_ai
if "%1"=="gui" goto :install_gui
if "%1"=="tts" goto :install_tts
if "%1"=="dev" goto :install_dev
if "%1"=="all" goto :install_all
if "%1"=="" goto :install_menu
goto :install_basic

:install_menu
echo.
echo %BOLD%%CYAN%  설치 옵션:%RESET%
echo.
echo   %GREEN%[1]%RESET% 기본 패키지       - 필수 의존성만 설치
echo   %GREEN%[2]%RESET% AI 패키지         - Wav2Vec2, HuBERT 등 AI 모델
echo   %GREEN%[3]%RESET% GUI 패키지        - PyQt6 GUI 의존성
echo   %GREEN%[4]%RESET% TTS 패키지        - gTTS, Edge-TTS 등
echo   %GREEN%[5]%RESET% 개발 패키지       - pytest, black, flake8 등
echo   %GREEN%[6]%RESET% 전체 패키지       - 모든 의존성 설치
echo   %GREEN%[0]%RESET% 뒤로 가기
echo.
set /p INSTALL_CHOICE="  선택 (0-6): "

if "%INSTALL_CHOICE%"=="1" goto :install_basic
if "%INSTALL_CHOICE%"=="2" goto :install_ai
if "%INSTALL_CHOICE%"=="3" goto :install_gui
if "%INSTALL_CHOICE%"=="4" goto :install_tts
if "%INSTALL_CHOICE%"=="5" goto :install_dev
if "%INSTALL_CHOICE%"=="6" goto :install_all
if "%INSTALL_CHOICE%"=="0" goto :interactive_menu

call :msg_error "잘못된 선택입니다."
goto :install_menu

:install_basic
call :msg_info "기본 의존성 설치 중..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
call :msg_success "기본 의존성 설치 완료!"
goto :eof

:install_ai
call :msg_info "AI 의존성 설치 중..."
python -m pip install --upgrade pip
if exist "requirements-ai.txt" (
    python -m pip install -r requirements-ai.txt
) else (
    python -m pip install ".[ai]"
)
call :msg_success "AI 의존성 설치 완료!"
goto :eof

:install_gui
call :msg_info "GUI 의존성 설치 중..."
python -m pip install --upgrade pip
if exist "requirements-gui.txt" (
    python -m pip install -r requirements-gui.txt
) else (
    python -m pip install ".[gui]"
)
call :msg_success "GUI 의존성 설치 완료!"
goto :eof

:install_tts
call :msg_info "TTS 의존성 설치 중..."
python -m pip install --upgrade pip
if exist "requirements-tts.txt" (
    python -m pip install -r requirements-tts.txt
) else (
    python -m pip install ".[tts]"
)
call :msg_success "TTS 의존성 설치 완료!"
goto :eof

:install_dev
call :msg_info "개발 의존성 설치 중..."
python -m pip install --upgrade pip
if exist "requirements-dev.txt" (
    python -m pip install -r requirements-dev.txt
) else (
    python -m pip install ".[dev]"
)
call :msg_success "개발 의존성 설치 완료!"
goto :eof

:install_all
call :msg_info "전체 의존성 설치 중..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if exist "requirements-ai.txt" python -m pip install -r requirements-ai.txt
if exist "requirements-gui.txt" python -m pip install -r requirements-gui.txt
if exist "requirements-tts.txt" python -m pip install -r requirements-tts.txt
if exist "requirements-dev.txt" python -m pip install -r requirements-dev.txt
call :msg_success "전체 의존성 설치 완료!"
goto :eof

REM ============================================================================
REM 프로젝트 정리
REM ============================================================================
:clean_project
echo.
call :msg_info "프로젝트 정리 중..."

REM Python 캐시 삭제
call :msg_info "__pycache__ 디렉토리 삭제 중..."
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul

REM pytest 캐시 삭제
call :msg_info ".pytest_cache 디렉토리 삭제 중..."
if exist ".pytest_cache" rd /s /q ".pytest_cache" 2>nul

REM mypy 캐시 삭제
call :msg_info ".mypy_cache 디렉토리 삭제 중..."
if exist ".mypy_cache" rd /s /q ".mypy_cache" 2>nul

REM 빌드 디렉토리 삭제
call :msg_info "빌드 디렉토리 삭제 중..."
if exist "build" rd /s /q "build" 2>nul
if exist "dist" rd /s /q "dist" 2>nul
if exist "*.egg-info" rd /s /q "*.egg-info" 2>nul

REM 커버리지 파일 삭제
call :msg_info "커버리지 파일 삭제 중..."
if exist ".coverage" del /q ".coverage" 2>nul
if exist "htmlcov" rd /s /q "htmlcov" 2>nul

REM .pyc 파일 삭제
call :msg_info ".pyc 파일 삭제 중..."
del /s /q *.pyc 2>nul

call :msg_success "프로젝트 정리 완료!"
goto :eof

REM ============================================================================
REM 도움말 출력
REM ============================================================================
:show_help
echo.
echo %BOLD%%CYAN%Personal Voice TTS AI - 사용법%RESET%
echo.
echo %YELLOW%사용법:%RESET%
echo   run.bat [명령어] [옵션]
echo.
echo %YELLOW%명령어:%RESET%
echo   %GREEN%web%RESET%      웹 서버 실행 (기본값)
echo            옵션: --host ^<호스트^>, --port/-p ^<포트^>
echo   %GREEN%gui%RESET%      GUI 애플리케이션 실행
echo   %GREEN%cli%RESET%      CLI 도구 실행
echo            서브명령: basic, similarity, synthesize, tts, batch
echo   %GREEN%test%RESET%     테스트 실행
echo            옵션: -v (상세), -q (간략), -c (커버리지)
echo   %GREEN%install%RESET%  의존성 설치
echo            옵션: basic, ai, gui, tts, dev, all
echo   %GREEN%clean%RESET%    캐시 및 빌드 파일 정리
echo   %GREEN%menu%RESET%     대화형 메뉴 표시
echo   %GREEN%help%RESET%     도움말 표시
echo.
echo %YELLOW%환경변수:%RESET%
echo   %CYAN%PVTTS_HOST%RESET%   웹 서버 호스트 (기본값: 0.0.0.0)
echo   %CYAN%PVTTS_PORT%RESET%   웹 서버 포트 (기본값: 8000)
echo   %CYAN%PVTTS_DEBUG%RESET%  디버그 모드 (1로 설정하면 활성화)
echo.
echo %YELLOW%예시:%RESET%
echo   run.bat                           # 대화형 메뉴
echo   run.bat web                       # 웹 서버 실행 (기본 포트)
echo   run.bat web --port 3000           # 웹 서버 (포트 3000)
echo   run.bat gui                       # GUI 실행
echo   run.bat cli basic info audio.wav  # CLI 오디오 정보
echo   run.bat test -v                   # 상세 테스트
echo   run.bat install all               # 전체 의존성 설치
echo   run.bat clean                     # 캐시 정리
echo.
echo   set PVTTS_PORT=3000               # 환경변수로 포트 설정
echo   run.bat web                       # 설정된 포트로 실행
echo.
goto :eof

REM ============================================================================
REM 메시지 출력 함수
REM ============================================================================
:msg_info
echo %BLUE%[INFO]%RESET% %~1
goto :eof

:msg_success
echo %GREEN%[SUCCESS]%RESET% %~1
goto :eof

:msg_warn
echo %YELLOW%[WARN]%RESET% %~1
goto :eof

:msg_error
echo %RED%[ERROR]%RESET% %~1
goto :eof

REM ============================================================================
REM 종료
REM ============================================================================
:exit_script
echo.
call :msg_info "프로그램을 종료합니다."
exit /b 0

:eof
endlocal
