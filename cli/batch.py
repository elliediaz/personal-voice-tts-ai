"""
Batch Processing CLI

배치 처리 CLI 모듈
"""

import sys
import json
from pathlib import Path

import click

from core.batch.processor import BatchProcessor
from core.batch.pipeline import Pipeline
from config import get_config
from utils.logging import setup_logger

logger = None


def init_logger(debug: bool = False):
    """로거를 초기화합니다."""
    global logger
    config = get_config()

    level = "DEBUG" if debug else config.logging.level

    logger = setup_logger(
        "batch",
        level=level,
        log_file=config.logging.file if not debug else None,
        console=config.logging.console,
    )

    return logger


@click.group()
@click.option('--debug', is_flag=True, help='디버그 모드 활성화')
@click.pass_context
def cli(ctx, debug):
    """
    Personal Voice TTS AI - Batch Processing CLI

    배치 처리 및 워크플로 자동화
    """
    ctx.ensure_object(dict)
    ctx.obj['logger'] = init_logger(debug)
    ctx.obj['debug'] = debug


@cli.command()
@click.argument('workflow', type=str)
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('source_paths', nargs=-1, type=click.Path(exists=True), required=True)
@click.option('--output-dir', '-o', type=click.Path(), required=True, help='출력 디렉토리')
@click.option('--max-workers', '-w', type=int, help='최대 워커 수')
@click.option('--use-processes', is_flag=True, help='프로세스 사용 (기본: 스레드)')
@click.option('--results', type=click.Path(), help='결과 저장 경로 (JSON)')
@click.pass_context
def run(ctx, workflow, input_file, source_paths, output_dir, max_workers, use_processes, results):
    """
    워크플로를 실행합니다.

    WORKFLOW: 워크플로 이름 (tts_collage, audio_matching, batch_synthesis)

    INPUT_FILE: 입력 파일 (텍스트 파일 또는 오디오 경로 리스트)

    SOURCE_PATHS: 소스 오디오 파일 경로들
    """
    logger = ctx.obj['logger']

    try:
        logger.info(f"배치 워크플로 시작: {workflow}")

        # 출력 디렉토리 생성
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 입력 파일 읽기
        with open(input_file, 'r', encoding='utf-8') as f:
            inputs = [line.strip() for line in f if line.strip()]

        click.echo(f"\n워크플로: {workflow}")
        click.echo(f"입력 개수: {len(inputs)}")
        click.echo(f"소스 파일 수: {len(source_paths)}")
        click.echo(f"출력 디렉토리: {output_dir}\n")

        # 배치 프로세서 생성
        processor = BatchProcessor(
            max_workers=max_workers,
            use_processes=use_processes,
            continue_on_error=True,
            show_progress=True,
        )

        # 워크플로에 따라 작업 생성
        if workflow == "tts_collage":
            from core.tts.backends import GTTSBackend
            from algorithms.traditional.mfcc import MFCCSimilarity
            from core.tts.pipeline import TTSPipeline

            tts_backend = GTTSBackend(language="ko")
            sim_algo = MFCCSimilarity()
            pipeline = TTSPipeline(tts_engine=tts_backend, similarity_algorithm=sim_algo)

            for i, text in enumerate(inputs, 1):
                output_path = output_dir / f"output_{i:03d}.wav"
                processor.add_job(
                    job_id=f"tts_collage_{i}",
                    func=pipeline.synthesize_collage,
                    kwargs={
                        "text": text,
                        "source_files": [Path(p) for p in source_paths],
                        "output_path": output_path,
                    },
                    priority=0,
                )

        elif workflow == "audio_matching":
            from core.synthesis.engine import CollageEngine
            from algorithms.traditional.mfcc import MFCCSimilarity

            sim_algo = MFCCSimilarity()
            engine = CollageEngine(similarity_algorithm=sim_algo)

            for i, audio_path in enumerate(inputs, 1):
                output_path = output_dir / f"output_{i:03d}.wav"
                processor.add_job(
                    job_id=f"audio_matching_{i}",
                    func=engine.synthesize_from_file,
                    kwargs={
                        "target_file": Path(audio_path),
                        "source_files": [Path(p) for p in source_paths],
                        "output_path": output_path,
                    },
                    priority=0,
                )

        else:
            click.echo(f"지원하지 않는 워크플로: {workflow}", err=True)
            sys.exit(1)

        # 배치 처리 실행
        summary = processor.process_all()

        # 결과 출력
        click.echo(f"\n\n배치 처리 완료!")
        click.echo(f"전체: {summary['total_count']}")
        click.echo(f"성공: {summary['success_count']}")
        click.echo(f"실패: {summary['error_count']}")
        click.echo(f"성공률: {summary['success_rate']:.1f}%")
        click.echo(f"소요 시간: {summary['total_time']:.2f}초")
        click.echo(f"처리 속도: {summary['jobs_per_second']:.2f} jobs/sec")

        # 결과 저장
        if results:
            processor.result_aggregator.save_json(Path(results))
            click.echo(f"\n결과 저장: {results}")

    except Exception as e:
        logger.error(f"오류 발생: {str(e)}", exc_info=ctx.obj['debug'])
        click.echo(f"\n오류: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--workflow', '-w', help='워크플로 이름 (비워두면 모두 표시)')
@click.pass_context
def list_workflows(ctx, workflow):
    """
    사용 가능한 워크플로 목록을 표시합니다.
    """
    logger = ctx.obj['logger']

    workflows_dir = Path("config/workflows")

    if not workflows_dir.exists():
        click.echo("워크플로 디렉토리를 찾을 수 없습니다.", err=True)
        sys.exit(1)

    workflow_files = list(workflows_dir.glob("*.yml"))

    if not workflow_files:
        click.echo("워크플로를 찾을 수 없습니다.", err=True)
        sys.exit(1)

    click.echo("\n사용 가능한 워크플로:\n")

    for wf_file in workflow_files:
        import yaml

        with open(wf_file, 'r', encoding='utf-8') as f:
            wf_config = yaml.safe_load(f)

        if workflow and wf_config.get('name') != workflow:
            continue

        click.echo(f"  {wf_config.get('name', wf_file.stem)}")
        click.echo(f"    설명: {wf_config.get('description', 'N/A').strip()}")
        click.echo(f"    스테이지 수: {len(wf_config.get('stages', []))}")
        click.echo()


@cli.command()
@click.argument('job_count', type=int)
@click.option('--max-workers', '-w', type=int, default=4, help='최대 워커 수')
@click.option('--use-processes', is_flag=True, help='프로세스 사용')
@click.pass_context
def benchmark(ctx, job_count, max_workers, use_processes):
    """
    배치 프로세서 성능 벤치마크를 실행합니다.

    JOB_COUNT: 테스트할 작업 수
    """
    import time
    import random

    logger = ctx.obj['logger']

    click.echo(f"\n배치 프로세서 벤치마크")
    click.echo(f"작업 수: {job_count}")
    click.echo(f"워커 수: {max_workers}")
    click.echo(f"실행 방식: {'프로세스' if use_processes else '스레드'}\n")

    def dummy_job(duration):
        """더미 작업"""
        time.sleep(duration)
        return f"Completed after {duration}s"

    # 배치 프로세서 생성
    processor = BatchProcessor(
        max_workers=max_workers,
        use_processes=use_processes,
        continue_on_error=True,
        show_progress=True,
    )

    # 작업 추가
    for i in range(job_count):
        duration = random.uniform(0.1, 0.5)
        processor.add_job(
            job_id=f"job_{i+1}",
            func=dummy_job,
            args=(duration,),
            priority=0,
        )

    # 실행
    summary = processor.process_all()

    # 결과
    click.echo(f"\n\n벤치마크 결과:")
    click.echo(f"전체 작업: {summary['total_count']}")
    click.echo(f"성공: {summary['success_count']}")
    click.echo(f"실패: {summary['error_count']}")
    click.echo(f"소요 시간: {summary['total_time']:.2f}초")
    click.echo(f"처리 속도: {summary['jobs_per_second']:.2f} jobs/sec")


def main():
    """CLI 진입점"""
    cli(obj={})


if __name__ == '__main__':
    main()


__all__ = ["cli", "main"]
