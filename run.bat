@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion

:: ============================================================================
:: Personal Voice TTS AI - 향상된 실행 스크립트 (Windows)
:: 버전: 1.0.0
:: ============================================================================
::
:: 사용법: run.bat [명령어] [옵션]
::
:: 명령어:
::   web      - 웹 서버 실행 (기본값)
::   gui      - GUI 애플리케이션 실행
::   cli      - CLI 도구 실행
::   test     - 테스트 실행
::   install  - 의존성 설치
::   setup    - 환경 설정 (가상환경 생성 + 의존성 설치)
::   status   - 환경 상태 표시
::   reset    - 환경 초기화
::   clean    - 캐시 및 빌드 파일 정리
::   help     - 도움말 표시
::
:: 환경변수:
::   PVTTS_HOST       - 웹 서버 호스트 (기본값: 0.0.0.0)
::   PVTTS_PORT       - 웹 서버 포트 (기본값: 8000)
::   PVTTS_DEBUG      - 디버그 모드 (1로 설정하면 활성화)
::   PVTTS_VENV_NAME  - 가상환경 디렉토리 이름 (기본값: venv)
::   PVTTS_AUTO_SETUP - 자동 환경 설정 (기본값: 1, 0으로 비활성화)
:: ============================================================================

:: 프로젝트 루트 디렉토리
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

:: ============================================================================
:: 환경 변수 기본값
:: ============================================================================
if not defined PVTTS_HOST set "PVTTS_HOST=0.0.0.0"
if not defined PVTTS_PORT set "PVTTS_PORT=8000"
if not defined PVTTS_DEBUG set "PVTTS_DEBUG=0"
if not defined PVTTS_VENV_NAME set "PVTTS_VENV_NAME=venv"
if not defined PVTTS_AUTO_SETUP set "PVTTS_AUTO_SETUP=1"

:: 설정 마커 파일
set "SETUP_MARKER=.pvtts_setup_done"

:: Python 경로 (나중에 설정됨)
set "PYTHON="

:: ============================================================================
:: 메인 진입점
:: ============================================================================
call :show_banner

set "COMMAND=%~1"
if "%COMMAND%"=="" set "COMMAND=menu"

:: Python 불필요한 명령어 먼저 처리
if /i "%COMMAND%"=="help" goto :show_help
if /i "%COMMAND%"=="--help" goto :show_help
if /i "%COMMAND%"=="-h" goto :show_help
if /i "%COMMAND%"=="clean" goto :clean_project
if /i "%COMMAND%"=="reset" (
    call :check_python
    goto :reset_environment
)

:: Python 필요한 명령어 - 환경 확인 및 준비
call :ensure_environment

if /i "%COMMAND%"=="web" goto :run_web
if /i "%COMMAND%"=="gui" goto :run_gui
if /i "%COMMAND%"=="cli" goto :run_cli
if /i "%COMMAND%"=="test" goto :run_test
if /i "%COMMAND%"=="install" goto :install_deps
if /i "%COMMAND%"=="setup" goto :run_setup
if /i "%COMMAND%"=="status" goto :show_status
if /i "%COMMAND%"=="menu" goto :interactive_menu

call :msg_error "알 수 없는 명령어: %COMMAND%"
goto :show_help

:: ============================================================================
:: 메시지 출력 함수
:: ============================================================================
:msg_info
echo [INFO] %~1
goto :eof

:msg_success
echo [SUCCESS] %~1
goto :eof

:msg_warn
echo [WARN] %~1
goto :eof

:msg_error
echo [ERROR] %~1
goto :eof

:msg_step
echo [STEP] %~1
goto :eof

:: ============================================================================
:: 배너 출력
:: ============================================================================
:show_banner
echo.
echo   ============================================================
echo    Personal Voice TTS AI v1.0.0
echo    음성 콜라주 및 합성 기반의 고급 TTS 시스템
echo   ============================================================
echo.
goto :eof

:: ============================================================================
:: Python 확인
:: ============================================================================
:check_python
:: py launcher 확인 (Windows 권장)
where py >nul 2>&1
if %errorlevel%==0 (
    set "PYTHON=py -3"
    goto :check_python_version
)

:: python 확인
where python >nul 2>&1
if %errorlevel%==0 (
    set "PYTHON=python"
    goto :check_python_version
)

:: python3 확인
where python3 >nul 2>&1
if %errorlevel%==0 (
    set "PYTHON=python3"
    goto :check_python_version
)

call :msg_error "Python이 설치되어 있지 않습니다."
call :msg_info "https://www.python.org/downloads/ 에서 Python 3.9 이상을 설치하세요."
exit /b 1

:check_python_version
:: Python 버전 확인
for /f "tokens=*" %%i in ('%PYTHON% -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"') do set "PYTHON_VERSION=%%i"
for /f "tokens=*" %%i in ('%PYTHON% -c "import sys; print(sys.version_info.major)"') do set "PYTHON_MAJOR=%%i"
for /f "tokens=*" %%i in ('%PYTHON% -c "import sys; print(sys.version_info.minor)"') do set "PYTHON_MINOR=%%i"

if %PYTHON_MAJOR% LSS 3 (
    call :msg_error "Python 3.9 이상이 필요합니다. 현재 버전: %PYTHON_VERSION%"
    exit /b 1
)
if %PYTHON_MAJOR%==3 if %PYTHON_MINOR% LSS 9 (
    call :msg_error "Python 3.9 이상이 필요합니다. 현재 버전: %PYTHON_VERSION%"
    exit /b 1
)

call :msg_info "Python %PYTHON_VERSION% 감지됨"
goto :eof

:: ============================================================================
:: 가상환경 존재 여부 확인
:: ============================================================================
:venv_exists
if exist "%PVTTS_VENV_NAME%\Scripts\activate.bat" (
    exit /b 0
)
if exist ".venv\Scripts\activate.bat" (
    set "PVTTS_VENV_NAME=.venv"
    exit /b 0
)
exit /b 1

:: ============================================================================
:: 가상환경 생성
:: ============================================================================
:create_venv
call :msg_step "가상환경 생성 중... (%PVTTS_VENV_NAME%)"

%PYTHON% -m venv "%PVTTS_VENV_NAME%"
if %errorlevel% neq 0 (
    call :msg_error "가상환경 생성 실패"
    exit /b 1
)

call :msg_success "가상환경 생성 완료: %PVTTS_VENV_NAME%"
goto :eof

:: ============================================================================
:: 가상환경 활성화
:: ============================================================================
:activate_venv
call :venv_exists
if %errorlevel%==0 (
    call :msg_info "가상환경 활성화 중... (%PVTTS_VENV_NAME%)"
    call "%PVTTS_VENV_NAME%\Scripts\activate.bat"
    set "PYTHON=%PVTTS_VENV_NAME%\Scripts\python.exe"
    call :msg_success "가상환경 활성화 완료"
    exit /b 0
) else (
    call :msg_warn "가상환경이 감지되지 않았습니다."
    exit /b 1
)

:: ============================================================================
:: pip 업그레이드
:: ============================================================================
:upgrade_pip
call :msg_step "pip 업그레이드 중..."
%PYTHON% -m pip install --upgrade pip --quiet
call :msg_success "pip 업그레이드 완료"
goto :eof

:: ============================================================================
:: 기본 의존성 설치 여부 확인
:: ============================================================================
:check_basic_deps
%PYTHON% -c "import numpy; import librosa; import fastapi" >nul 2>&1
exit /b %errorlevel%

:: ============================================================================
:: 의존성 설치 (기본)
:: ============================================================================
:install_basic_deps
call :msg_step "기본 의존성 설치 중..."

if exist "requirements.txt" (
    %PYTHON% -m pip install -r requirements.txt --quiet
    call :msg_success "기본 의존성 설치 완료"
) else (
    call :msg_error "requirements.txt 파일을 찾을 수 없습니다."
    exit /b 1
)
goto :eof

:: ============================================================================
:: 선택적 의존성 설치
:: ============================================================================
:install_optional_deps
set "DEP_TYPE=%~1"
set "REQ_FILE=requirements-%DEP_TYPE%.txt"

if exist "%REQ_FILE%" (
    call :msg_step "%DEP_TYPE% 의존성 설치 중..."
    %PYTHON% -m pip install -r "%REQ_FILE%" --quiet
    call :msg_success "%DEP_TYPE% 의존성 설치 완료"
) else (
    call :msg_warn "%REQ_FILE% 파일을 찾을 수 없습니다."
)
goto :eof

:: ============================================================================
:: 자동 환경 설정 (첫 실행 시)
:: ============================================================================
:auto_setup
set "NEED_SETUP=0"

:: 마커 파일 확인
if not exist "%SETUP_MARKER%" set "NEED_SETUP=1"

:: 가상환경 확인
call :venv_exists
if %errorlevel% neq 0 set "NEED_SETUP=1"

if "%NEED_SETUP%"=="1" (
    echo.
    echo ============================================================================
    echo   첫 실행 감지 - 환경 자동 설정을 시작합니다
    echo ============================================================================
    echo.

    :: 가상환경 생성
    call :venv_exists
    if !errorlevel! neq 0 (
        call :create_venv
    )

    :: 가상환경 활성화
    call :activate_venv

    :: pip 업그레이드
    call :upgrade_pip

    :: 기본 의존성 설치
    call :check_basic_deps
    if !errorlevel! neq 0 (
        call :install_basic_deps
    )

    :: 마커 파일 생성
    echo setup_date=%date% %time%> "%SETUP_MARKER%"
    echo python_version=%PYTHON_VERSION%>> "%SETUP_MARKER%"
    echo venv_name=%PVTTS_VENV_NAME%>> "%SETUP_MARKER%"

    echo.
    echo ============================================================================
    echo   환경 설정 완료!
    echo ============================================================================
    echo.
)
goto :eof

:: ============================================================================
:: 환경 확인 및 준비 (메인 진입점)
:: ============================================================================
:ensure_environment
call :check_python

:: 자동 설정이 활성화된 경우
if "%PVTTS_AUTO_SETUP%"=="1" (
    call :auto_setup
)

:: 가상환경 활성화 시도
call :venv_exists
if %errorlevel%==0 (
    call :activate_venv
) else (
    call :msg_warn "가상환경이 없습니다. 시스템 Python을 사용합니다."
    call :msg_info "가상환경 생성: run.bat setup"
)

:: 의존성 확인
call :check_basic_deps
if %errorlevel% neq 0 (
    call :msg_warn "필수 의존성이 설치되어 있지 않습니다."
    call :msg_info "의존성 설치: run.bat install basic"

    if "%PVTTS_AUTO_SETUP%"=="1" (
        echo.
        set /p "INSTALL_CHOICE=  지금 기본 의존성을 설치하시겠습니까? (Y/n): "
        if /i not "!INSTALL_CHOICE!"=="n" (
            call :install_basic_deps
        )
    )
)
goto :eof

:: ============================================================================
:: 전체 환경 설정 (수동)
:: ============================================================================
:run_setup
echo.
echo   환경 설정 옵션:
echo.
echo   [1] 기본 설정        - 가상환경 + 필수 의존성
echo   [2] GUI 포함 설정    - 기본 + PyQt6 GUI
echo   [3] TTS 포함 설정    - 기본 + TTS 백엔드
echo   [4] 전체 설정        - 모든 의존성 설치
echo   [5] 개발 환경 설정   - 전체 + 개발 도구
echo   [0] 취소
echo.
set /p "SETUP_CHOICE=  선택 (0-5): "

if "%SETUP_CHOICE%"=="1" goto :setup_basic
if "%SETUP_CHOICE%"=="2" goto :setup_with_gui
if "%SETUP_CHOICE%"=="3" goto :setup_with_tts
if "%SETUP_CHOICE%"=="4" goto :setup_full
if "%SETUP_CHOICE%"=="5" goto :setup_dev
if "%SETUP_CHOICE%"=="0" goto :eof

call :msg_error "잘못된 선택입니다."
goto :run_setup

:setup_basic
call :msg_info "기본 환경 설정 시작..."
call :check_python

call :venv_exists
if %errorlevel% neq 0 (
    call :create_venv
)

call :activate_venv
call :upgrade_pip
call :install_basic_deps

echo setup_date=%date% %time%> "%SETUP_MARKER%"
echo setup_type=basic>> "%SETUP_MARKER%"

call :msg_success "기본 환경 설정 완료!"
goto :eof

:setup_with_gui
call :setup_basic
call :install_optional_deps gui
echo setup_type=gui>> "%SETUP_MARKER%"
call :msg_success "GUI 포함 환경 설정 완료!"
goto :eof

:setup_with_tts
call :setup_basic
call :install_optional_deps tts
echo setup_type=tts>> "%SETUP_MARKER%"
call :msg_success "TTS 포함 환경 설정 완료!"
goto :eof

:setup_full
call :setup_basic
call :install_optional_deps gui
call :install_optional_deps tts
call :install_optional_deps ai
echo setup_type=full>> "%SETUP_MARKER%"
call :msg_success "전체 환경 설정 완료!"
goto :eof

:setup_dev
call :setup_full
call :install_optional_deps dev
echo setup_type=dev>> "%SETUP_MARKER%"
call :msg_success "개발 환경 설정 완료!"
goto :eof

:: ============================================================================
:: 환경 상태 표시
:: ============================================================================
:show_status
echo.
echo   환경 상태:
echo.

:: Python
for /f "tokens=*" %%i in ('%PYTHON% -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"') do set "PY_VER=%%i"
echo   Python:        %PY_VER%

:: 가상환경
call :venv_exists
if %errorlevel%==0 (
    echo   가상환경:      %PVTTS_VENV_NAME%
) else (
    echo   가상환경:      없음
)

:: 설정 마커
if exist "%SETUP_MARKER%" (
    for /f "tokens=1,* delims==" %%a in ('findstr "setup_date" "%SETUP_MARKER%"') do echo   설정 일시:     %%b
    for /f "tokens=1,* delims==" %%a in ('findstr "setup_type" "%SETUP_MARKER%"') do echo   설정 유형:     %%b
) else (
    echo   설정 상태:     미설정
)

echo.
echo   의존성 상태:

:: numpy
%PYTHON% -c "import numpy" >nul 2>&1
if %errorlevel%==0 (echo     numpy:       설치됨) else (echo     numpy:       미설치)

:: librosa
%PYTHON% -c "import librosa" >nul 2>&1
if %errorlevel%==0 (echo     librosa:     설치됨) else (echo     librosa:     미설치)

:: fastapi
%PYTHON% -c "import fastapi" >nul 2>&1
if %errorlevel%==0 (echo     fastapi:     설치됨) else (echo     fastapi:     미설치)

:: PyQt6
%PYTHON% -c "import PyQt6" >nul 2>&1
if %errorlevel%==0 (echo     PyQt6:       설치됨) else (echo     PyQt6:       미설치)

:: gTTS
%PYTHON% -c "import gtts" >nul 2>&1
if %errorlevel%==0 (echo     gTTS:        설치됨) else (echo     gTTS:        미설치)

:: edge-tts
%PYTHON% -c "import edge_tts" >nul 2>&1
if %errorlevel%==0 (echo     edge-tts:    설치됨) else (echo     edge-tts:    미설치)

echo.
goto :eof

:: ============================================================================
:: 웹 서버 실행
:: ============================================================================
:run_web
set "HOST=%PVTTS_HOST%"
set "PORT=%PVTTS_PORT%"

:parse_web_args
shift
if "%~1"=="" goto :start_web
if /i "%~1"=="--host" (
    set "HOST=%~2"
    shift
    goto :parse_web_args
)
if /i "%~1"=="--port" (
    set "PORT=%~2"
    shift
    goto :parse_web_args
)
if /i "%~1"=="-p" (
    set "PORT=%~2"
    shift
    goto :parse_web_args
)
goto :parse_web_args

:start_web
echo.
call :msg_info "웹 서버 시작 중..."
call :msg_info "호스트: %HOST%"
call :msg_info "포트: %PORT%"
echo.
call :msg_success "브라우저에서 http://localhost:%PORT% 로 접속하세요"
echo.

if "%PVTTS_DEBUG%"=="1" (
    %PYTHON% -m uvicorn web.app:app --host %HOST% --port %PORT% --reload --log-level debug
) else (
    %PYTHON% -m uvicorn web.app:app --host %HOST% --port %PORT% --reload
)
goto :eof

:: ============================================================================
:: GUI 실행
:: ============================================================================
:run_gui
echo.
call :msg_info "GUI 애플리케이션 시작 중..."

:: PyQt6 확인
%PYTHON% -c "import PyQt6" >nul 2>&1
if %errorlevel% neq 0 (
    call :msg_error "PyQt6가 설치되어 있지 않습니다."
    call :msg_info "설치 명령: run.bat install gui"

    set /p "INSTALL_CHOICE=  지금 GUI 의존성을 설치하시겠습니까? (Y/n): "
    if /i not "!INSTALL_CHOICE!"=="n" (
        call :install_optional_deps gui
    ) else (
        goto :eof
    )
)

%PYTHON% -m gui.app
goto :eof

:: ============================================================================
:: CLI 도구 실행
:: ============================================================================
:run_cli
shift
if "%~1"=="" goto :cli_menu
%PYTHON% -m cli.%*
goto :eof

:cli_menu
echo.
echo   CLI 도구 선택:
echo.
echo   [1] basic      - 기본 오디오 처리 (info, spectrogram, waveform)
echo   [2] similarity - 유사도 검출 (find, compare, batch)
echo   [3] synthesize - 오디오 합성 (collage, blend)
echo   [4] tts        - TTS 변환 (speak, collage, batch)
echo   [5] batch      - 배치 처리 (run, list-workflows, monitor)
echo   [0] 뒤로 가기
echo.
set /p "CLI_CHOICE=  선택 (0-5): "

if "%CLI_CHOICE%"=="1" (
    call :msg_info "CLI basic 도움말:"
    %PYTHON% -m cli.basic --help
    goto :cli_menu
)
if "%CLI_CHOICE%"=="2" (
    call :msg_info "CLI similarity 도움말:"
    %PYTHON% -m cli.similarity --help
    goto :cli_menu
)
if "%CLI_CHOICE%"=="3" (
    call :msg_info "CLI synthesize 도움말:"
    %PYTHON% -m cli.synthesize --help
    goto :cli_menu
)
if "%CLI_CHOICE%"=="4" (
    call :msg_info "CLI tts 도움말:"
    %PYTHON% -m cli.tts --help
    goto :cli_menu
)
if "%CLI_CHOICE%"=="5" (
    call :msg_info "CLI batch 도움말:"
    %PYTHON% -m cli.batch --help
    goto :cli_menu
)
if "%CLI_CHOICE%"=="0" goto :interactive_menu

call :msg_error "잘못된 선택입니다."
goto :cli_menu

:: ============================================================================
:: 테스트 실행
:: ============================================================================
:run_test
shift
set "TEST_OPT=%~1"

:: pytest 확인
%PYTHON% -c "import pytest" >nul 2>&1
if %errorlevel% neq 0 (
    call :msg_error "pytest가 설치되어 있지 않습니다."
    call :msg_info "설치 명령: run.bat install dev"

    set /p "INSTALL_CHOICE=  지금 개발 의존성을 설치하시겠습니까? (Y/n): "
    if /i not "!INSTALL_CHOICE!"=="n" (
        call :install_optional_deps dev
    ) else (
        goto :eof
    )
)

if /i "%TEST_OPT%"=="--verbose" goto :test_verbose
if /i "%TEST_OPT%"=="-v" goto :test_verbose
if /i "%TEST_OPT%"=="--quiet" goto :test_quiet
if /i "%TEST_OPT%"=="-q" goto :test_quiet
if /i "%TEST_OPT%"=="--coverage" goto :test_coverage
if /i "%TEST_OPT%"=="-c" goto :test_coverage
if "%TEST_OPT%"=="" goto :test_menu

call :msg_info "테스트 실행 중..."
%PYTHON% -m pytest tests/ --tb=short
goto :eof

:test_verbose
call :msg_info "상세 테스트 실행 중..."
%PYTHON% -m pytest tests/ -v --tb=short
goto :eof

:test_quiet
call :msg_info "간략 테스트 실행 중..."
%PYTHON% -m pytest tests/ -q
goto :eof

:test_coverage
call :msg_info "커버리지 테스트 실행 중..."
%PYTHON% -m pytest tests/ --cov=core --cov=algorithms --cov=web --cov=gui --cov-report=html --cov-report=term
call :msg_success "HTML 커버리지 리포트: htmlcov\index.html"
goto :eof

:test_menu
echo.
echo   테스트 옵션:
echo.
echo   [1] 기본 테스트       - pytest 기본 실행
echo   [2] 상세 테스트       - pytest -v (상세 출력)
echo   [3] 간략 테스트       - pytest -q (간략 출력)
echo   [4] 커버리지 테스트   - pytest --cov (커버리지 포함)
echo   [0] 뒤로 가기
echo.
set /p "TEST_CHOICE=  선택 (0-4): "

if "%TEST_CHOICE%"=="1" (
    call :msg_info "테스트 실행 중..."
    %PYTHON% -m pytest tests/ --tb=short
    goto :eof
)
if "%TEST_CHOICE%"=="2" goto :test_verbose
if "%TEST_CHOICE%"=="3" goto :test_quiet
if "%TEST_CHOICE%"=="4" goto :test_coverage
if "%TEST_CHOICE%"=="0" goto :interactive_menu

call :msg_error "잘못된 선택입니다."
goto :test_menu

:: ============================================================================
:: 의존성 설치
:: ============================================================================
:install_deps
shift
set "INSTALL_TYPE=%~1"

if /i "%INSTALL_TYPE%"=="basic" goto :install_basic
if /i "%INSTALL_TYPE%"=="ai" goto :install_ai
if /i "%INSTALL_TYPE%"=="gui" goto :install_gui
if /i "%INSTALL_TYPE%"=="tts" goto :install_tts
if /i "%INSTALL_TYPE%"=="dev" goto :install_dev
if /i "%INSTALL_TYPE%"=="all" goto :install_all
if "%INSTALL_TYPE%"=="" goto :install_menu

goto :install_basic

:install_menu
echo.
echo   설치 옵션:
echo.
echo   [1] 기본 패키지       - 필수 의존성만 설치
echo   [2] AI 패키지         - Wav2Vec2, HuBERT 등 AI 모델
echo   [3] GUI 패키지        - PyQt6 GUI 의존성
echo   [4] TTS 패키지        - gTTS, Edge-TTS 등
echo   [5] 개발 패키지       - pytest, black, flake8 등
echo   [6] 전체 패키지       - 모든 의존성 설치
echo   [0] 뒤로 가기
echo.
set /p "INSTALL_CHOICE=  선택 (0-6): "

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
%PYTHON% -m pip install --upgrade pip
%PYTHON% -m pip install -r requirements.txt
call :msg_success "기본 의존성 설치 완료!"
goto :eof

:install_ai
call :msg_info "AI 의존성 설치 중..."
%PYTHON% -m pip install --upgrade pip
if exist "requirements-ai.txt" (
    %PYTHON% -m pip install -r requirements-ai.txt
) else (
    %PYTHON% -m pip install ".[ai]"
)
call :msg_success "AI 의존성 설치 완료!"
goto :eof

:install_gui
call :msg_info "GUI 의존성 설치 중..."
%PYTHON% -m pip install --upgrade pip
if exist "requirements-gui.txt" (
    %PYTHON% -m pip install -r requirements-gui.txt
) else (
    %PYTHON% -m pip install ".[gui]"
)
call :msg_success "GUI 의존성 설치 완료!"
goto :eof

:install_tts
call :msg_info "TTS 의존성 설치 중..."
%PYTHON% -m pip install --upgrade pip
if exist "requirements-tts.txt" (
    %PYTHON% -m pip install -r requirements-tts.txt
) else (
    %PYTHON% -m pip install ".[tts]"
)
call :msg_success "TTS 의존성 설치 완료!"
goto :eof

:install_dev
call :msg_info "개발 의존성 설치 중..."
%PYTHON% -m pip install --upgrade pip
if exist "requirements-dev.txt" (
    %PYTHON% -m pip install -r requirements-dev.txt
) else (
    %PYTHON% -m pip install ".[dev]"
)
call :msg_success "개발 의존성 설치 완료!"
goto :eof

:install_all
call :msg_info "전체 의존성 설치 중..."
%PYTHON% -m pip install --upgrade pip
%PYTHON% -m pip install -r requirements.txt
if exist "requirements-ai.txt" %PYTHON% -m pip install -r requirements-ai.txt
if exist "requirements-gui.txt" %PYTHON% -m pip install -r requirements-gui.txt
if exist "requirements-tts.txt" %PYTHON% -m pip install -r requirements-tts.txt
if exist "requirements-dev.txt" %PYTHON% -m pip install -r requirements-dev.txt
call :msg_success "전체 의존성 설치 완료!"
goto :eof

:: ============================================================================
:: 프로젝트 정리
:: ============================================================================
:clean_project
echo.
call :msg_info "프로젝트 정리 중..."

:: Python 캐시 삭제
call :msg_info "__pycache__ 디렉토리 삭제 중..."
for /d /r %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul

:: .pyc 파일 삭제
call :msg_info ".pyc 파일 삭제 중..."
del /s /q *.pyc 2>nul

:: pytest 캐시 삭제
call :msg_info ".pytest_cache 디렉토리 삭제 중..."
if exist ".pytest_cache" rd /s /q ".pytest_cache" 2>nul

:: mypy 캐시 삭제
call :msg_info ".mypy_cache 디렉토리 삭제 중..."
if exist ".mypy_cache" rd /s /q ".mypy_cache" 2>nul

:: 빌드 디렉토리 삭제
call :msg_info "빌드 디렉토리 삭제 중..."
if exist "build" rd /s /q "build" 2>nul
if exist "dist" rd /s /q "dist" 2>nul
for /d %%d in (*.egg-info) do @if exist "%%d" rd /s /q "%%d" 2>nul

:: 커버리지 파일 삭제
call :msg_info "커버리지 파일 삭제 중..."
if exist ".coverage" del /q ".coverage" 2>nul
if exist "htmlcov" rd /s /q "htmlcov" 2>nul

call :msg_success "프로젝트 정리 완료!"
goto :eof

:: ============================================================================
:: 환경 초기화 (가상환경 삭제)
:: ============================================================================
:reset_environment
echo.
call :msg_warn "이 작업은 가상환경과 설정을 모두 삭제합니다."
set /p "RESET_CHOICE=  계속하시겠습니까? (y/N): "

if /i "%RESET_CHOICE%"=="y" (
    call :msg_info "환경 초기화 중..."

    :: 가상환경 삭제
    if exist "%PVTTS_VENV_NAME%" (
        rd /s /q "%PVTTS_VENV_NAME%"
        call :msg_info "가상환경 삭제됨: %PVTTS_VENV_NAME%"
    )

    if exist ".venv" (
        rd /s /q ".venv"
        call :msg_info "가상환경 삭제됨: .venv"
    )

    :: 마커 파일 삭제
    if exist "%SETUP_MARKER%" (
        del /q "%SETUP_MARKER%"
        call :msg_info "설정 마커 삭제됨"
    )

    call :clean_project

    call :msg_success "환경 초기화 완료!"
    call :msg_info "다시 실행하면 환경이 자동으로 설정됩니다."
) else (
    call :msg_info "취소되었습니다."
)
goto :eof

:: ============================================================================
:: 도움말 출력
:: ============================================================================
:show_help
echo.
echo   Personal Voice TTS AI - 사용법
echo   ============================================================
echo.
echo   사용법: run.bat [명령어] [옵션]
echo.
echo   명령어:
echo     web      웹 서버 실행 (기본값)
echo              옵션: --host ^<호스트^>, --port/-p ^<포트^>
echo     gui      GUI 애플리케이션 실행
echo     cli      CLI 도구 실행
echo              서브명령: basic, similarity, synthesize, tts, batch
echo     test     테스트 실행
echo              옵션: -v (상세), -q (간략), -c (커버리지)
echo     install  의존성 설치
echo              옵션: basic, ai, gui, tts, dev, all
echo     setup    환경 설정 (가상환경 생성 + 의존성 설치)
echo     status   환경 상태 표시
echo     reset    환경 초기화 (가상환경 삭제)
echo     clean    캐시 및 빌드 파일 정리
echo     menu     대화형 메뉴 표시
echo     help     도움말 표시
echo.
echo   환경변수:
echo     PVTTS_HOST       웹 서버 호스트 (기본값: 0.0.0.0)
echo     PVTTS_PORT       웹 서버 포트 (기본값: 8000)
echo     PVTTS_DEBUG      디버그 모드 (1로 설정하면 활성화)
echo     PVTTS_VENV_NAME  가상환경 디렉토리 이름 (기본값: venv)
echo     PVTTS_AUTO_SETUP 자동 환경 설정 (기본값: 1, 0으로 비활성화)
echo.
echo   예시:
echo     run.bat                           대화형 메뉴 (첫 실행 시 자동 설정)
echo     run.bat setup                     환경 수동 설정
echo     run.bat web                       웹 서버 실행 (기본 포트)
echo     run.bat web --port 3000           웹 서버 (포트 3000)
echo     run.bat gui                       GUI 실행
echo     run.bat cli basic info audio.wav  CLI 오디오 정보
echo     run.bat test -v                   상세 테스트
echo     run.bat install all               전체 의존성 설치
echo     run.bat status                    환경 상태 확인
echo     run.bat reset                     환경 초기화
echo     run.bat clean                     캐시 정리
echo.
echo     set PVTTS_AUTO_SETUP=0            자동 설정 비활성화
echo     run.bat web
echo.
goto :eof

:: ============================================================================
:: 대화형 메뉴
:: ============================================================================
:interactive_menu
echo.
echo   메뉴를 선택하세요:
echo.
echo   [1] 웹 서버 실행         - FastAPI 웹 서비스 시작
echo   [2] GUI 실행             - PyQt6 GUI 애플리케이션 시작
echo   [3] CLI 도구             - CLI 명령어 도움말
echo   [4] 테스트 실행          - pytest 테스트 스위트 실행
echo   [5] 의존성 설치          - pip 패키지 설치
echo   [6] 환경 설정            - 가상환경 + 의존성 설정
echo   [7] 환경 상태            - 현재 환경 정보 표시
echo   [8] 정리                 - 캐시 및 빌드 파일 삭제
echo   [9] 도움말               - 상세 사용법 표시
echo   [0] 종료
echo.
set /p "MENU_CHOICE=  선택 (0-9): "

if "%MENU_CHOICE%"=="1" goto :run_web
if "%MENU_CHOICE%"=="2" goto :run_gui
if "%MENU_CHOICE%"=="3" goto :cli_menu
if "%MENU_CHOICE%"=="4" goto :test_menu
if "%MENU_CHOICE%"=="5" goto :install_menu
if "%MENU_CHOICE%"=="6" goto :run_setup
if "%MENU_CHOICE%"=="7" goto :show_status
if "%MENU_CHOICE%"=="8" goto :clean_project
if "%MENU_CHOICE%"=="9" goto :show_help
if "%MENU_CHOICE%"=="0" (
    echo.
    call :msg_info "프로그램을 종료합니다."
    exit /b 0
)

call :msg_error "잘못된 선택입니다. 0-9 사이의 숫자를 입력하세요."
goto :interactive_menu
