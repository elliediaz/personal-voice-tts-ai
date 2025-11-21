"""
Basic CLI Module

기본적인 오디오 파일 처리를 위한 CLI 명령어를 제공합니다.
"""

import sys
from pathlib import Path
from typing import Optional

import click

from core.audio.io import AudioFile
from core.audio.analysis import AudioAnalyzer
from core.audio.metadata import AudioMetadata
from config import get_config, reload_config
from utils.logging import setup_logger, get_logger

# 로거 초기화
logger = None


def init_logger(debug: bool = False):
    """로거를 초기화합니다."""
    global logger
    config = get_config()

    level = "DEBUG" if debug else config.logging.level
    log_file = config.logging.file if not debug else None

    logger = setup_logger(
        "voice-tts",
        level=level,
        log_file=log_file,
        console=config.logging.console,
        log_format=config.logging.format,
        date_format=config.logging.date_format,
    )

    return logger


@click.group()
@click.option('--debug', is_flag=True, help='디버그 모드 활성화')
@click.option('--config', type=click.Path(exists=True), help='설정 파일 경로')
@click.pass_context
def cli(ctx, debug, config):
    """
    Personal Voice TTS AI - 기본 CLI 도구

    오디오 파일 로딩, 분석, 시각화 등의 기본 기능을 제공합니다.
    """
    # 설정 로드
    if config:
        reload_config(config)

    # 로거 초기화
    ctx.ensure_object(dict)
    ctx.obj['logger'] = init_logger(debug)
    ctx.obj['debug'] = debug


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--json', 'output_json', is_flag=True, help='JSON 형식으로 출력')
@click.pass_context
def info(ctx, file_path, output_json):
    """
    오디오 파일의 정보를 표시합니다.

    FILE_PATH: 분석할 오디오 파일 경로
    """
    logger = ctx.obj['logger']

    try:
        logger.info(f"오디오 파일 정보 조회: {file_path}")

        # 오디오 파일 로드
        audio = AudioFile.load(file_path)

        # 메타데이터 추출
        metadata = AudioMetadata.from_audio_file(
            Path(file_path),
            audio.data,
            audio.sample_rate,
            compute_fingerprint=True,
            compute_statistics=True,
        )

        # 출력
        if output_json:
            click.echo(metadata.to_json())
        else:
            click.echo("\n=== 오디오 파일 정보 ===\n")
            click.echo(f"파일 이름: {metadata.file_name}")
            click.echo(f"파일 경로: {metadata.file_path}")
            click.echo(f"파일 크기: {metadata.file_size:,} bytes ({metadata.file_size/1024/1024:.2f} MB)")
            click.echo(f"파일 포맷: {metadata.format.upper()}")
            click.echo(f"\n샘플링 레이트: {metadata.sample_rate:,} Hz")
            click.echo(f"채널 수: {metadata.channels}")
            click.echo(f"길이: {metadata.duration:.2f}초 ({metadata.duration/60:.2f}분)")
            click.echo(f"총 샘플 수: {metadata.num_samples:,}")

            if metadata.statistics:
                click.echo(f"\n=== 통계 정보 ===")
                click.echo(f"평균: {metadata.statistics['mean']:.6f}")
                click.echo(f"표준편차: {metadata.statistics['std']:.6f}")
                click.echo(f"최소값: {metadata.statistics['min']:.6f}")
                click.echo(f"최대값: {metadata.statistics['max']:.6f}")
                click.echo(f"중앙값: {metadata.statistics['median']:.6f}")
                click.echo(f"RMS: {metadata.statistics['rms']:.6f}")

            if metadata.fingerprint:
                click.echo(f"\n지문(MD5): {metadata.fingerprint}")

        logger.info("오디오 파일 정보 조회 완료")

    except Exception as e:
        logger.error(f"오류 발생: {str(e)}", exc_info=ctx.obj['debug'])
        sys.exit(1)


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='출력 파일 경로')
@click.option('--type', 'spec_type', type=click.Choice(['spectrogram', 'mel']), default='spectrogram', help='스펙트로그램 타입')
@click.option('--dpi', type=int, default=100, help='출력 DPI')
@click.pass_context
def spectrogram(ctx, file_path, output, spec_type, dpi):
    """
    오디오 파일의 스펙트로그램을 생성합니다.

    FILE_PATH: 분석할 오디오 파일 경로
    """
    logger = ctx.obj['logger']

    try:
        logger.info(f"스펙트로그램 생성 시작: {file_path}")

        # 오디오 파일 로드
        audio = AudioFile.load(file_path, mono=True)

        # 분석기 생성
        analyzer = AudioAnalyzer()

        # 스펙트로그램 계산 및 시각화
        if spec_type == 'spectrogram':
            spec = analyzer.compute_spectrogram(audio.data, audio.sample_rate)
            fig = analyzer.visualize_spectrogram(spec, audio.sample_rate, title=f"Spectrogram - {Path(file_path).name}")
        else:  # mel
            mel_spec = analyzer.compute_mel_spectrogram(audio.data, audio.sample_rate)
            fig = analyzer.visualize_mel_spectrogram(mel_spec, audio.sample_rate, title=f"Mel Spectrogram - {Path(file_path).name}")

        # 저장 또는 표시
        if output:
            fig.savefig(output, dpi=dpi, bbox_inches='tight')
            logger.info(f"스펙트로그램 저장 완료: {output}")
            click.echo(f"스펙트로그램 저장 완료: {output}")
        else:
            import matplotlib.pyplot as plt
            plt.show()

        logger.info("스펙트로그램 생성 완료")

    except Exception as e:
        logger.error(f"오류 발생: {str(e)}", exc_info=ctx.obj['debug'])
        sys.exit(1)


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='출력 파일 경로')
@click.option('--dpi', type=int, default=100, help='출력 DPI')
@click.pass_context
def waveform(ctx, file_path, output, dpi):
    """
    오디오 파일의 파형을 표시합니다.

    FILE_PATH: 분석할 오디오 파일 경로
    """
    logger = ctx.obj['logger']

    try:
        logger.info(f"파형 표시 시작: {file_path}")

        # 오디오 파일 로드
        audio = AudioFile.load(file_path)

        # 분석기 생성
        analyzer = AudioAnalyzer()

        # 파형 시각화
        fig = analyzer.visualize_waveform(audio.data, audio.sample_rate, title=f"Waveform - {Path(file_path).name}")

        # 저장 또는 표시
        if output:
            fig.savefig(output, dpi=dpi, bbox_inches='tight')
            logger.info(f"파형 저장 완료: {output}")
            click.echo(f"파형 저장 완료: {output}")
        else:
            import matplotlib.pyplot as plt
            plt.show()

        logger.info("파형 표시 완료")

    except Exception as e:
        logger.error(f"오류 발생: {str(e)}", exc_info=ctx.obj['debug'])
        sys.exit(1)


@cli.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.argument('output_path', type=click.Path())
@click.option('--format', '-f', type=str, help='출력 포맷 (wav, mp3, flac, ogg)')
@click.option('--sample-rate', '-sr', type=int, help='샘플링 레이트')
@click.option('--mono', is_flag=True, help='모노로 변환')
@click.option('--normalize', is_flag=True, help='정규화')
@click.pass_context
def convert(ctx, input_path, output_path, format, sample_rate, mono, normalize):
    """
    오디오 파일을 변환합니다.

    INPUT_PATH: 입력 오디오 파일 경로
    OUTPUT_PATH: 출력 파일 경로
    """
    logger = ctx.obj['logger']

    try:
        logger.info(f"오디오 변환 시작: {input_path} -> {output_path}")

        # 오디오 파일 로드
        audio = AudioFile.load(input_path)

        # 모노 변환
        if mono:
            audio = audio.to_mono()

        # 리샘플링
        if sample_rate:
            audio = audio.resample(sample_rate)

        # 정규화
        if normalize:
            audio = audio.normalize()

        # 저장
        audio.save(output_path, format=format)

        logger.info(f"오디오 변환 완료: {output_path}")
        click.echo(f"오디오 변환 완료: {output_path}")

    except Exception as e:
        logger.error(f"오류 발생: {str(e)}", exc_info=ctx.obj['debug'])
        sys.exit(1)


def main():
    """CLI 진입점"""
    cli(obj={})


if __name__ == '__main__':
    main()


__all__ = ["cli", "main"]
