"""
Similarity CLI Module

유사도 검출을 위한 CLI 명령어를 제공합니다.
"""

import sys
import json
from pathlib import Path

import click

from core.audio.io import AudioFile
from core.similarity.manager import AlgorithmManager
from config import get_config
from utils.logging import setup_logger

logger = None


def init_logger(debug: bool = False):
    """로거를 초기화합니다."""
    global logger
    config = get_config()

    level = "DEBUG" if debug else config.logging.level

    logger = setup_logger(
        "similarity",
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
    Personal Voice TTS AI - 유사도 검출 CLI 도구

    오디오 파일 간의 유사도를 분석하고 유사 세그먼트를 찾습니다.
    """
    ctx.ensure_object(dict)
    ctx.obj['logger'] = init_logger(debug)
    ctx.obj['debug'] = debug


@cli.command()
@click.argument('target_path', type=click.Path(exists=True))
@click.argument('source_path', type=click.Path(exists=True))
@click.option('--algorithm', '-a', default='mfcc', help='사용할 알고리즘 (mfcc, spectral, energy, rhythm, random)')
@click.option('--top-k', '-k', type=int, default=10, help='반환할 최대 매치 수')
@click.option('--output', '-o', type=click.Path(), help='결과 저장 경로 (JSON)')
@click.pass_context
def find(ctx, target_path, source_path, algorithm, top_k, output):
    """
    타겟 오디오와 유사한 소스 오디오의 세그먼트를 찾습니다.

    TARGET_PATH: 타겟 오디오 파일 경로
    SOURCE_PATH: 소스 오디오 파일 경로
    """
    logger = ctx.obj['logger']

    try:
        logger.info(f"유사 세그먼트 검색 시작...")
        logger.info(f"타겟: {target_path}")
        logger.info(f"소스: {source_path}")
        logger.info(f"알고리즘: {algorithm}")

        # 오디오 로드
        target = AudioFile.load(target_path)
        source = AudioFile.load(source_path)

        # 알고리즘 매니저 생성
        manager = AlgorithmManager()

        # 유사 세그먼트 찾기
        matches = manager.find_similar_segments(
            algorithm,
            target.data,
            source.data,
            target.sample_rate,
            source.sample_rate,
            top_k=top_k,
        )

        # 결과 출력
        click.echo(f"\n{len(matches)}개의 유사 세그먼트 발견:\n")

        for i, match in enumerate(matches, 1):
            click.echo(f"{i}. 유사도: {match.similarity:.3f}")
            click.echo(f"   소스 위치: {match.source_start:.2f}s ~ {match.source_end:.2f}s")
            click.echo(f"   길이: {match.source_duration:.2f}s")
            click.echo()

        # JSON 저장 (옵션)
        if output:
            result_data = {
                'target': str(target_path),
                'source': str(source_path),
                'algorithm': algorithm,
                'num_matches': len(matches),
                'matches': [
                    {
                        'similarity': m.similarity,
                        'confidence': m.confidence,
                        'source_start': m.source_start,
                        'source_end': m.source_end,
                        'source_duration': m.source_duration,
                        'metadata': m.metadata,
                    }
                    for m in matches
                ]
            }

            with open(output, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False)

            logger.info(f"결과 저장 완료: {output}")
            click.echo(f"\n결과 저장: {output}")

    except Exception as e:
        logger.error(f"오류 발생: {str(e)}", exc_info=ctx.obj['debug'])
        sys.exit(1)


@cli.command()
@click.argument('target_path', type=click.Path(exists=True))
@click.argument('source_path', type=click.Path(exists=True))
@click.option('--algorithms', '-a', multiple=True, default=['mfcc', 'spectral'], help='사용할 알고리즘들')
@click.option('--top-k', '-k', type=int, default=10, help='반환할 최대 매치 수')
@click.option('--output', '-o', type=click.Path(), help='결과 저장 경로 (JSON)')
@click.pass_context
def ensemble(ctx, target_path, source_path, algorithms, top_k, output):
    """
    여러 알고리즘을 앙상블하여 유사 세그먼트를 찾습니다.

    TARGET_PATH: 타겟 오디오 파일 경로
    SOURCE_PATH: 소스 오디오 파일 경로
    """
    logger = ctx.obj['logger']

    try:
        logger.info(f"앙상블 검색 시작...")
        logger.info(f"알고리즘: {list(algorithms)}")

        # 오디오 로드
        target = AudioFile.load(target_path)
        source = AudioFile.load(source_path)

        # 알고리즘 매니저 생성
        manager = AlgorithmManager()

        # 앙상블 검색
        matches = manager.ensemble_find_segments(
            list(algorithms),
            target.data,
            source.data,
            target.sample_rate,
            source.sample_rate,
            top_k=top_k,
        )

        # 결과 출력
        click.echo(f"\n{len(matches)}개의 유사 세그먼트 발견 (앙상블):\n")

        for i, match in enumerate(matches, 1):
            click.echo(f"{i}. 유사도: {match.similarity:.3f}, 신뢰도: {match.confidence:.3f}")
            click.echo(f"   소스 위치: {match.source_start:.2f}s ~ {match.source_end:.2f}s")
            click.echo(f"   투표 수: {match.metadata.get('num_votes', 0)}")
            click.echo()

        # JSON 저장 (옵션)
        if output:
            result_data = {
                'target': str(target_path),
                'source': str(source_path),
                'algorithms': list(algorithms),
                'num_matches': len(matches),
                'matches': [
                    {
                        'similarity': m.similarity,
                        'confidence': m.confidence,
                        'source_start': m.source_start,
                        'source_end': m.source_end,
                        'metadata': m.metadata,
                    }
                    for m in matches
                ]
            }

            with open(output, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False)

            click.echo(f"\n결과 저장: {output}")

    except Exception as e:
        logger.error(f"오류 발생: {str(e)}", exc_info=ctx.obj['debug'])
        sys.exit(1)


@cli.command()
@click.option('--test-duration', '-d', type=float, default=3.0, help='테스트 오디오 길이 (초)')
@click.pass_context
def benchmark(ctx, test_duration):
    """
    등록된 모든 알고리즘의 성능을 벤치마크합니다.
    """
    logger = ctx.obj['logger']

    try:
        import numpy as np

        logger.info("벤치마크 시작...")

        # 테스트 오디오 생성
        sr = 22050
        target_audio = np.random.randn(int(test_duration * sr)).astype(np.float32)
        source_audio = np.random.randn(int(test_duration * 5 * sr)).astype(np.float32)

        # 알고리즘 매니저 생성
        manager = AlgorithmManager()

        # 벤치마크 실행
        results = manager.benchmark_algorithms(
            target_audio=target_audio,
            source_audio=source_audio,
            target_sr=sr,
            source_sr=sr,
        )

        # 결과 출력
        click.echo("\n=== 벤치마크 결과 ===\n")

        for name, result in results.items():
            if result.get('success'):
                click.echo(f"{name}:")
                click.echo(f"  매치 수: {result['num_matches']}")
                click.echo(f"  소요 시간: {result['elapsed_time']:.3f}초")
                click.echo(f"  평균 유사도: {result['avg_similarity']:.3f}")
                click.echo()
            else:
                click.echo(f"{name}: 실패 - {result.get('error')}")
                click.echo()

    except Exception as e:
        logger.error(f"오류 발생: {str(e)}", exc_info=ctx.obj['debug'])
        sys.exit(1)


@cli.command()
def list_algorithms():
    """등록된 모든 알고리즘을 나열합니다."""
    manager = AlgorithmManager()
    algorithms = manager.list_algorithms()

    click.echo("\n사용 가능한 알고리즘:\n")
    for algo in algorithms:
        click.echo(f"  - {algo}")
    click.echo()


def main():
    """CLI 진입점"""
    cli(obj={})


if __name__ == '__main__':
    main()


__all__ = ["cli", "main"]
