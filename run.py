#!/usr/bin/env python3
"""
Personal Voice TTS AI - 크로스플랫폼 실행 스크립트

이 스크립트는 Linux, macOS, Windows 등 모든 플랫폼에서 동일하게 작동합니다.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path


def get_project_root():
    """프로젝트 루트 디렉토리 반환"""
    return Path(__file__).parent.absolute()


def run_web_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = True):
    """웹 서버 실행"""
    print(f"[INFO] 웹 서버 시작...")
    print(f"[INFO] 접속 주소: http://localhost:{port}")

    try:
        import uvicorn
        uvicorn.run(
            "web.app:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except ImportError:
        print("[ERROR] uvicorn이 설치되어 있지 않습니다.")
        print("[INFO] 'pip install uvicorn' 명령으로 설치해주세요.")
        sys.exit(1)


def run_cli(args: list):
    """CLI 도구 실행"""
    if not args:
        print("[INFO] 사용 가능한 CLI 명령어:")
        print("  basic     - 기본 오디오 처리")
        print("  similarity - 유사도 검출")
        print("  synthesize - 오디오 합성")
        print("  tts       - TTS 변환")
        print("  batch     - 배치 처리")
        print()
        print("예시: python run.py cli basic info audio.wav")
        return

    module = f"cli.{args[0]}"
    cmd = [sys.executable, "-m", module] + args[1:]
    subprocess.run(cmd)


def run_gui():
    """GUI 애플리케이션 실행"""
    print("[INFO] GUI 애플리케이션 시작...")
    subprocess.run([sys.executable, "-m", "gui.app"])


def run_tests(verbose: bool = True):
    """테스트 실행"""
    print("[INFO] 테스트 실행 중...")
    cmd = [sys.executable, "-m", "pytest", "tests/"]
    if verbose:
        cmd.extend(["-v", "--tb=short"])
    subprocess.run(cmd)


def install_dependencies(extras: str = None):
    """의존성 설치"""
    print("[INFO] 의존성 설치 중...")

    # pip 업그레이드
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])

    # 기본 의존성
    req_file = "requirements.txt"
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", req_file])

    # 추가 의존성
    if extras:
        extras_map = {
            "ai": "requirements-ai.txt",
            "gui": "requirements-gui.txt",
            "tts": "requirements-tts.txt",
            "dev": "requirements-dev.txt",
            "all": ["requirements-ai.txt", "requirements-gui.txt",
                    "requirements-tts.txt", "requirements-dev.txt"]
        }

        if extras in extras_map:
            files = extras_map[extras]
            if isinstance(files, str):
                files = [files]
            for f in files:
                if Path(f).exists():
                    subprocess.run([sys.executable, "-m", "pip", "install", "-r", f])

    print("[INFO] 의존성 설치 완료")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="Personal Voice TTS AI 실행 스크립트",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python run.py                    # 웹 서버 실행
  python run.py web --port 3000    # 3000 포트로 웹 서버 실행
  python run.py cli basic info a.wav  # CLI 오디오 정보 조회
  python run.py test               # 테스트 실행
  python run.py install --extras all  # 모든 의존성 설치
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="실행할 명령어")

    # web 서브커맨드
    web_parser = subparsers.add_parser("web", help="웹 서버 실행")
    web_parser.add_argument("--host", default="0.0.0.0", help="호스트 (기본값: 0.0.0.0)")
    web_parser.add_argument("--port", type=int, default=8000, help="포트 (기본값: 8000)")
    web_parser.add_argument("--no-reload", action="store_true", help="자동 리로드 비활성화")

    # cli 서브커맨드
    cli_parser = subparsers.add_parser("cli", help="CLI 도구 실행")
    cli_parser.add_argument("cli_args", nargs="*", help="CLI 인자")

    # gui 서브커맨드
    subparsers.add_parser("gui", help="GUI 애플리케이션 실행")

    # test 서브커맨드
    test_parser = subparsers.add_parser("test", help="테스트 실행")
    test_parser.add_argument("-q", "--quiet", action="store_true", help="간략한 출력")

    # install 서브커맨드
    install_parser = subparsers.add_parser("install", help="의존성 설치")
    install_parser.add_argument(
        "--extras",
        choices=["ai", "gui", "tts", "dev", "all"],
        help="추가 의존성 (ai, gui, tts, dev, all)"
    )

    args = parser.parse_args()

    # 프로젝트 루트로 이동
    os.chdir(get_project_root())

    # 명령어 실행
    if args.command is None or args.command == "web":
        host = getattr(args, "host", "0.0.0.0")
        port = getattr(args, "port", 8000)
        reload = not getattr(args, "no_reload", False)
        run_web_server(host=host, port=port, reload=reload)
    elif args.command == "cli":
        run_cli(args.cli_args)
    elif args.command == "gui":
        run_gui()
    elif args.command == "test":
        run_tests(verbose=not args.quiet)
    elif args.command == "install":
        install_dependencies(extras=args.extras)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
