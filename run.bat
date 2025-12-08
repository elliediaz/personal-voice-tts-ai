@echo off
REM Personal Voice TTS AI - 실행 스크립트 (Windows)
REM 사용법: run.bat [명령어]
REM
REM 명령어:
REM   web      - 웹 서버 실행 (기본값)
REM   cli      - CLI 도구 실행
REM   test     - 테스트 실행
REM   install  - 의존성 설치

setlocal enabledelayedexpansion

REM 프로젝트 디렉토리로 이동
cd /d "%~dp0"

REM 기본값 설정
if "%HOST%"=="" set HOST=0.0.0.0
if "%PORT%"=="" set PORT=8000

REM Python 확인
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python이 설치되어 있지 않습니다.
    exit /b 1
)

REM Python 버전 출력
echo [INFO] Python 버전:
python --version

REM 가상환경 활성화
if exist "venv\Scripts\activate.bat" (
    echo [INFO] 가상환경 활성화...
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    echo [INFO] 가상환경 활성화...
    call .venv\Scripts\activate.bat
)

REM 명령어 처리
set COMMAND=%1
if "%COMMAND%"=="" set COMMAND=web

if "%COMMAND%"=="web" goto :run_web
if "%COMMAND%"=="cli" goto :run_cli
if "%COMMAND%"=="gui" goto :run_gui
if "%COMMAND%"=="test" goto :run_test
if "%COMMAND%"=="install" goto :install_deps
if "%COMMAND%"=="help" goto :show_help
if "%COMMAND%"=="--help" goto :show_help
if "%COMMAND%"=="-h" goto :show_help

echo [ERROR] 알 수 없는 명령어: %COMMAND%
goto :show_help

:run_web
echo [INFO] 웹 서버 시작...
echo [INFO] 접속 주소: http://localhost:%PORT%
python -m uvicorn web.app:app --host %HOST% --port %PORT% --reload
goto :eof

:run_cli
shift
if "%1"=="" (
    echo [INFO] 사용 가능한 CLI 명령어:
    echo   basic     - 기본 오디오 처리
    echo   similarity - 유사도 검출
    echo   synthesize - 오디오 합성
    echo   tts       - TTS 변환
    echo   batch     - 배치 처리
    echo.
    echo 예시: run.bat cli basic info audio.wav
) else (
    python -m cli.%*
)
goto :eof

:run_gui
echo [INFO] GUI 애플리케이션 시작...
python -m gui.app
goto :eof

:run_test
echo [INFO] 테스트 실행 중...
python -m pytest tests/ -v --tb=short
goto :eof

:install_deps
echo [INFO] 의존성 설치 중...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo [INFO] 의존성 설치 완료
goto :eof

:show_help
echo Personal Voice TTS AI - 실행 스크립트
echo.
echo 사용법: run.bat [명령어] [옵션]
echo.
echo 명령어:
echo   web      웹 서버 실행 (기본값)
echo   cli      CLI 도구 실행
echo   gui      GUI 애플리케이션 실행
echo   test     테스트 실행
echo   install  의존성 설치
echo   help     도움말 표시
echo.
echo 환경변수:
echo   HOST     웹 서버 호스트 (기본값: 0.0.0.0)
echo   PORT     웹 서버 포트 (기본값: 8000)
echo.
echo 예시:
echo   run.bat                       웹 서버 실행
echo   run.bat web                   웹 서버 실행
echo   run.bat cli basic info a.wav  CLI 오디오 정보 조회
echo   run.bat test                  테스트 실행
echo   set PORT=3000 ^& run.bat web  3000 포트로 웹 서버 실행
goto :eof
