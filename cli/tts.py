"""
TTS CLI Module

TTS 및 TTS-to-Collage 워크플로를 위한 CLI 명령어를 제공합니다.
"""

import sys
import json
from pathlib import Path

import click

from core.tts.backends import GTTSBackend, Pyttsx3Backend, EdgeTTSBackend
from core.tts.preprocessing import TextPreprocessor
from core.tts.pipeline import TTSPipeline
from core.tts.batch import BatchTTSProcessor
from algorithms.traditional.mfcc import MFCCSimilarity
from algorithms.ai_based.embedding_matcher import EmbeddingSimilarity
from algorithms.ai_based.hybrid import HybridSimilarity
from config import get_config
from utils.logging import setup_logger

logger = None


def init_logger(debug: bool = False):
    """로거를 초기화합니다."""
    global logger
    config = get_config()

    level = "DEBUG" if debug else config.logging.level

    logger = setup_logger(
        "tts",
        level=level,
        log_file=config.logging.file if not debug else None,
        console=config.logging.console,
    )

    return logger


def get_tts_backend(backend_name: str, language: str = "ko"):
    """TTS 백엔드 생성"""
    if backend_name == "gtts":
        return GTTSBackend(language=language)
    elif backend_name == "pyttsx3":
        return Pyttsx3Backend(language=language)
    elif backend_name == "edge":
        lang_map = {"ko": "ko-KR", "en": "en-US", "ja": "ja-JP"}
        return EdgeTTSBackend(language=lang_map.get(language, "ko-KR"))
    else:
        raise ValueError(f"지원하지 않는 백엔드: {backend_name}")


def get_similarity_algorithm(algorithm_name: str):
    """유사도 알고리즘 생성"""
    if algorithm_name == "mfcc":
        return MFCCSimilarity()
    elif algorithm_name == "spectral":
        from algorithms.traditional.spectral import SpectralSimilarity
        return SpectralSimilarity()
    elif algorithm_name == "embedding":
        return EmbeddingSimilarity(device='cpu')
    elif algorithm_name == "hybrid":
        return HybridSimilarity()
    else:
        raise ValueError(f"지원하지 않는 알고리즘: {algorithm_name}")


@click.group()
@click.option('--debug', is_flag=True, help='디버그 모드 활성화')
@click.pass_context
def cli(ctx, debug):
    """
    Personal Voice TTS AI - TTS CLI 도구

    텍스트 음성 변환 및 TTS-to-Collage 워크플로
    """
    ctx.ensure_object(dict)
    ctx.obj['logger'] = init_logger(debug)
    ctx.obj['debug'] = debug


@cli.command()
@click.argument('text', type=str)
@click.option('--output', '-o', type=click.Path(), required=True, help='출력 파일 경로')
@click.option('--backend', '-b', default='gtts', help='TTS 백엔드 (gtts, pyttsx3, edge)')
@click.option('--language', '-l', default='ko', help='언어 코드 (ko, en, ja)')
@click.pass_context
def speak(ctx, text, output, backend, language):
    """
    텍스트를 음성으로 변환합니다.

    TEXT: 변환할 텍스트
    """
    logger = ctx.obj['logger']

    try:
        logger.info(f"TTS 시작: {len(text)}자")

        # TTS 백엔드 생성
        tts_backend = get_tts_backend(backend, language)

        click.echo(f"\n백엔드: {tts_backend.__class__.__name__}")
        click.echo(f"언어: {language}")
        click.echo(f"텍스트: {text}\n")

        # TTS 실행
        audio_data, sample_rate = tts_backend.synthesize(text, output_path=Path(output))

        click.echo(f"TTS 완료: {output}")
        click.echo(f"길이: {len(audio_data) / sample_rate:.2f}초")

    except Exception as e:
        logger.error(f"오류 발생: {str(e)}", exc_info=ctx.obj['debug'])
        click.echo(f"\n오류: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('text', type=str)
@click.argument('source_paths', nargs=-1, type=click.Path(exists=True), required=True)
@click.option('--output', '-o', type=click.Path(), required=True, help='출력 파일 경로')
@click.option('--backend', '-b', default='gtts', help='TTS 백엔드')
@click.option('--algorithm', '-a', default='mfcc', help='유사도 알고리즘')
@click.option('--language', '-l', default='ko', help='언어 코드')
@click.option('--metadata', type=click.Path(), help='메타데이터 저장 경로 (JSON)')
@click.pass_context
def collage(ctx, text, source_paths, output, backend, algorithm, language, metadata):
    """
    텍스트를 콜라주 음성으로 변환합니다 (TTS + Collage).

    TEXT: 변환할 텍스트

    SOURCE_PATHS: 소스 오디오 파일 경로들
    """
    logger = ctx.obj['logger']

    try:
        logger.info(f"TTS-to-Collage 시작: {len(text)}자")

        # TTS 백엔드 생성
        tts_backend = get_tts_backend(backend, language)

        # 유사도 알고리즘 생성
        sim_algo = get_similarity_algorithm(algorithm)

        # 파이프라인 생성
        pipeline = TTSPipeline(
            tts_engine=tts_backend,
            similarity_algorithm=sim_algo,
        )

        click.echo(f"\nTTS 백엔드: {tts_backend.__class__.__name__}")
        click.echo(f"유사도 알고리즘: {sim_algo.__class__.__name__}")
        click.echo(f"소스 파일 수: {len(source_paths)}")
        click.echo(f"텍스트: {text}\n")

        # TTS-to-Collage 실행
        source_file_paths = [Path(p) for p in source_paths]

        collage_metadata = pipeline.synthesize_collage(
            text=text,
            source_files=source_file_paths,
            output_path=Path(output),
        )

        click.echo(f"\n콜라주 완료!")
        click.echo(f"출력 파일: {output}")
        click.echo(f"처리 시간: {collage_metadata['processing_time']:.2f}초")
        click.echo(f"최고 유사도: {collage_metadata['similarity']:.3f}")
        click.echo(f"소스 파일: {collage_metadata['source_file']}")

        # 메타데이터 저장 (옵션)
        if metadata:
            with open(metadata, 'w', encoding='utf-8') as f:
                json.dump(collage_metadata, f, indent=2, ensure_ascii=False)

            click.echo(f"\n메타데이터 저장: {metadata}")

    except Exception as e:
        logger.error(f"오류 발생: {str(e)}", exc_info=ctx.obj['debug'])
        click.echo(f"\n오류: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('source_paths', nargs=-1, type=click.Path(exists=True), required=True)
@click.option('--output-dir', '-o', type=click.Path(), required=True, help='출력 디렉토리')
@click.option('--backend', '-b', default='gtts', help='TTS 백엔드')
@click.option('--algorithm', '-a', default='mfcc', help='유사도 알고리즘')
@click.option('--language', '-l', default='ko', help='언어 코드')
@click.pass_context
def batch(ctx, input_file, source_paths, output_dir, backend, algorithm, language):
    """
    파일에서 텍스트를 읽어 배치 처리합니다.

    INPUT_FILE: 입력 텍스트 파일 (각 줄이 하나의 텍스트)

    SOURCE_PATHS: 소스 오디오 파일 경로들
    """
    logger = ctx.obj['logger']

    try:
        logger.info(f"배치 TTS-to-Collage 시작: {input_file}")

        # TTS 백엔드 생성
        tts_backend = get_tts_backend(backend, language)

        # 유사도 알고리즘 생성
        sim_algo = get_similarity_algorithm(algorithm)

        # 파이프라인 생성
        pipeline = TTSPipeline(
            tts_engine=tts_backend,
            similarity_algorithm=sim_algo,
        )

        # 배치 프로세서 생성
        batch_processor = BatchTTSProcessor(pipeline)

        click.echo(f"\nTTS 백엔드: {tts_backend.__class__.__name__}")
        click.echo(f"유사도 알고리즘: {sim_algo.__class__.__name__}")
        click.echo(f"입력 파일: {input_file}")
        click.echo(f"출력 디렉토리: {output_dir}\n")

        # 배치 처리
        source_file_paths = [Path(p) for p in source_paths]

        results = batch_processor.process_from_file(
            input_file=Path(input_file),
            source_files=source_file_paths,
            output_dir=Path(output_dir),
        )

        # 결과 요약
        success_count = sum(1 for r in results if r.get("success", False))
        click.echo(f"\n배치 처리 완료!")
        click.echo(f"성공: {success_count}/{len(results)}")
        click.echo(f"출력 디렉토리: {output_dir}")

    except Exception as e:
        logger.error(f"오류 발생: {str(e)}", exc_info=ctx.obj['debug'])
        click.echo(f"\n오류: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--backend', '-b', default='gtts', help='TTS 백엔드')
@click.pass_context
def list_voices(ctx, backend):
    """
    사용 가능한 음성 목록을 표시합니다.
    """
    logger = ctx.obj['logger']

    try:
        # TTS 백엔드 생성
        tts_backend = get_tts_backend(backend, "ko")

        voices = tts_backend.get_available_voices()

        click.echo(f"\n{backend} 백엔드 사용 가능한 음성:\n")
        for voice in voices:
            click.echo(f"  - {voice}")

    except Exception as e:
        logger.error(f"오류 발생: {str(e)}", exc_info=ctx.obj['debug'])
        click.echo(f"\n오류: {str(e)}", err=True)
        sys.exit(1)


def main():
    """CLI 진입점"""
    cli(obj={})


if __name__ == '__main__':
    main()


__all__ = ["cli", "main"]
