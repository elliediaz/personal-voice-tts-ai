"""
Web Application

FastAPI 기반 웹 애플리케이션 메인 모듈
"""

import os
import uuid
import tempfile
import logging
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
import aiofiles

from config import get_config
from core.audio.io import AudioFile
from core.audio.analysis import AudioAnalyzer
from core.tts.preprocessing import TextPreprocessor

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="Personal Voice TTS AI",
    description="음성 콜라주 및 합성 기반 TTS 시스템 API",
    version="0.1.0",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 경로 설정
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
UPLOAD_DIR = Path(tempfile.gettempdir()) / "voice_tts_uploads"
OUTPUT_DIR = Path(tempfile.gettempdir()) / "voice_tts_outputs"

# 디렉토리 생성
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 정적 파일 및 템플릿 설정
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# 설정 로드
config = get_config()

# 분석기 인스턴스
analyzer = AudioAnalyzer()

# 전처리기 인스턴스
preprocessor = TextPreprocessor(language="ko")


@app.get("/")
async def index(request: Request):
    """메인 페이지"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/health")
async def health_check():
    """서비스 상태 확인"""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "service": "Personal Voice TTS AI"
    }


@app.get("/api/info")
async def service_info():
    """서비스 정보 조회"""
    return {
        "name": "Personal Voice TTS AI",
        "version": "0.1.0",
        "description": "음성 콜라주 및 합성 기반 TTS 시스템",
        "features": [
            "오디오 분석",
            "유사도 검출",
            "음성 합성",
            "TTS 변환",
            "배치 처리"
        ],
        "supported_formats": config.audio.supported_formats
    }


@app.post("/api/audio/analyze")
async def analyze_audio(file: UploadFile = File(...)):
    """오디오 파일 분석"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="파일명이 필요합니다")

    # 파일 확장자 확인
    ext = Path(file.filename).suffix.lower().lstrip(".")
    if ext not in config.audio.supported_formats:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 형식입니다: {ext}"
        )

    # 임시 파일 저장
    file_id = str(uuid.uuid4())
    temp_path = UPLOAD_DIR / f"{file_id}.{ext}"

    try:
        async with aiofiles.open(temp_path, "wb") as f:
            content = await file.read()
            await f.write(content)

        # 오디오 로드 및 분석
        audio_file = AudioFile.load(temp_path)

        # 기본 분석
        analysis_result = {
            "file_id": file_id,
            "filename": file.filename,
            "sample_rate": audio_file.sample_rate,
            "channels": audio_file.channels,
            "duration": float(audio_file.duration),
            "num_samples": audio_file.num_samples,
        }

        # 스펙트럼 분석
        if len(audio_file.data) > 0:
            mono_data = audio_file.to_mono().data
            analysis_result["spectral_centroid"] = float(
                analyzer.compute_spectral_centroid(mono_data, audio_file.sample_rate).mean()
            )
            analysis_result["rms_energy"] = float(
                analyzer.compute_energy(mono_data).mean()
            )

        return analysis_result

    except Exception as e:
        logger.error(f"오디오 분석 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"분석 실패: {str(e)}")

    finally:
        # 임시 파일 삭제
        if temp_path.exists():
            temp_path.unlink()


@app.post("/api/text/preprocess")
async def preprocess_text(
    text: str = Form(...),
    language: str = Form(default="ko")
):
    """텍스트 전처리"""
    try:
        proc = TextPreprocessor(language=language)
        processed = proc.preprocess(text)
        sentences = proc.split_sentences(processed)

        return {
            "original": text,
            "processed": processed,
            "sentences": sentences,
            "language": language
        }
    except Exception as e:
        logger.error(f"텍스트 전처리 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"전처리 실패: {str(e)}")


@app.get("/api/algorithms")
async def list_algorithms():
    """사용 가능한 알고리즘 목록"""
    from core.similarity.manager import AlgorithmManager

    manager = AlgorithmManager()
    algorithms = manager.list_algorithms()

    return {
        "algorithms": algorithms,
        "count": len(algorithms)
    }


@app.post("/api/audio/upload")
async def upload_audio(file: UploadFile = File(...)):
    """오디오 파일 업로드"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="파일명이 필요합니다")

    ext = Path(file.filename).suffix.lower().lstrip(".")
    if ext not in config.audio.supported_formats:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 형식입니다: {ext}"
        )

    file_id = str(uuid.uuid4())
    save_path = UPLOAD_DIR / f"{file_id}.{ext}"

    try:
        async with aiofiles.open(save_path, "wb") as f:
            content = await file.read()
            await f.write(content)

        return {
            "file_id": file_id,
            "filename": file.filename,
            "path": str(save_path),
            "size": len(content)
        }
    except Exception as e:
        logger.error(f"파일 업로드 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"업로드 실패: {str(e)}")


@app.get("/api/audio/download/{file_id}")
async def download_audio(file_id: str):
    """오디오 파일 다운로드"""
    # 업로드 디렉토리와 출력 디렉토리에서 파일 검색
    for directory in [UPLOAD_DIR, OUTPUT_DIR]:
        for path in directory.glob(f"{file_id}.*"):
            if path.exists():
                return FileResponse(
                    path=str(path),
                    filename=path.name,
                    media_type="audio/wav"
                )

    raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")


def cleanup_file(path: Path):
    """파일 정리 (백그라운드 작업용)"""
    try:
        if path.exists():
            path.unlink()
    except Exception as e:
        logger.warning(f"파일 정리 실패: {str(e)}")


# 서버 실행 함수
def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """웹 서버 실행"""
    import uvicorn
    uvicorn.run(
        "web.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    run_server()
