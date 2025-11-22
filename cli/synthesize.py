"""
Synthesize CLI Module

오디오 합성을 위한 CLI 명령어를 제공합니다.
"""

import sys
import json
from pathlib import Path

import click

from core.audio.io import AudioFile
from core.synthesis.engine import CollageEngine
from core.synthesis.metrics import QualityMetrics
from algorithms.traditional.mfcc import MFCCSimilarity
from algorithms.ai_based.embedding_matcher import EmbeddingSimilarity
from algorithms.ai_based.hybrid import HybridSimilarity
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
        "synthesize",
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
    Personal Voice TTS AI - 오디오 합성 CLI 도구

    타겟 오디오를 소스 파일들로부터 합성하는 콜라주 도구
    """
    ctx.ensure_object(dict)
    ctx.obj['logger'] = init_logger(debug)
    ctx.obj['debug'] = debug


@cli.command()
@click.argument('target_path', type=click.Path(exists=True))
@click.argument('source_paths', nargs=-1, type=click.Path(exists=True), required=True)
@click.option('--output', '-o', type=click.Path(), required=True, help='출력 파일 경로')
@click.option('--algorithm', '-a', default='mfcc', help='유사도 알고리즘 (mfcc, spectral, embedding, hybrid)')
@click.option('--top-k', '-k', type=int, default=1, help='각 소스에서 찾을 매치 수')
@click.option('--no-pitch', is_flag=True, help='피치 조정 비활성화')
@click.option('--no-tempo', is_flag=True, help='템포 조정 비활성화')
@click.option('--no-prosody', is_flag=True, help='프로소디 매칭 비활성화')
@click.option('--no-enhance', is_flag=True, help='품질 향상 비활성화')
@click.option('--metadata', type=click.Path(), help='메타데이터 저장 경로 (JSON)')
@click.pass_context
def synthesize(ctx, target_path, source_paths, output, algorithm, top_k,
               no_pitch, no_tempo, no_prosody, no_enhance, metadata):
    """
    타겟 오디오를 소스 파일들로부터 합성합니다.

    TARGET_PATH: 타겟 오디오 파일 경로

    SOURCE_PATHS: 소스 오디오 파일 경로들
    """
    logger = ctx.obj['logger']

    try:
        logger.info(f"합성 시작: {target_path} -> {output}")
        logger.info(f"소스 파일 수: {len(source_paths)}")

        # 알고리즘 선택
        if algorithm == 'mfcc':
            sim_algo = MFCCSimilarity()
        elif algorithm == 'spectral':
            from algorithms.traditional.spectral import SpectralSimilarity
            sim_algo = SpectralSimilarity()
        elif algorithm == 'embedding':
            sim_algo = EmbeddingSimilarity(device='cpu')
        elif algorithm == 'hybrid':
            sim_algo = HybridSimilarity()
        else:
            raise ValueError(f"지원하지 않는 알고리즘: {algorithm}")

        click.echo(f"\n사용 알고리즘: {sim_algo.__class__.__name__}\n")

        # 콜라주 엔진 생성
        engine = CollageEngine(similarity_algorithm=sim_algo)

        # 진행률 콜백
        def progress_callback(progress, message):
            percentage = int(progress * 100)
            click.echo(f"[{percentage:3d}%] {message}")

        # 합성
        source_file_paths = [Path(p) for p in source_paths]

        synth_metadata = engine.synthesize_from_file(
            target_file=Path(target_path),
            source_files=source_file_paths,
            output_file=Path(output),
            top_k=top_k,
            adjust_pitch=not no_pitch,
            adjust_tempo=not no_tempo,
            match_prosody=not no_prosody,
            enhance_quality=not no_enhance,
            progress_callback=progress_callback,
        )

        click.echo(f"\n합성 완료!")
        click.echo(f"출력 파일: {output}")
        click.echo(f"처리 시간: {synth_metadata['processing_time']:.2f}초")
        click.echo(f"최고 유사도: {synth_metadata['similarity']:.3f}")
        click.echo(f"소스 파일: {synth_metadata['source_file']}")
        click.echo(f"소스 구간: {synth_metadata['source_start']:.2f}s ~ {synth_metadata['source_end']:.2f}s")

        # 메타데이터 저장 (옵션)
        if metadata:
            with open(metadata, 'w', encoding='utf-8') as f:
                json.dump(synth_metadata, f, indent=2, ensure_ascii=False)

            click.echo(f"\n메타데이터 저장: {metadata}")

    except Exception as e:
        logger.error(f"오류 발생: {str(e)}", exc_info=ctx.obj['debug'])
        click.echo(f"\n오류: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('audio_path', type=click.Path(exists=True))
@click.option('--reference', '-r', type=click.Path(exists=True), help='참조 오디오 (비교용)')
@click.option('--output', '-o', type=click.Path(), help='결과 저장 경로 (JSON)')
@click.pass_context
def analyze(ctx, audio_path, reference, output):
    """
    오디오 품질을 분석합니다.

    AUDIO_PATH: 분석할 오디오 파일 경로
    """
    logger = ctx.obj['logger']

    try:
        logger.info(f"품질 분석 시작: {audio_path}")

        # 오디오 로드
        audio = AudioFile.load(audio_path)

        # 참조 오디오 로드 (옵션)
        ref_audio_data = None
        if reference:
            ref_audio = AudioFile.load(reference)
            ref_audio_data = ref_audio.data

        # 품질 분석
        metrics = QualityMetrics()
        results = metrics.analyze_quality(
            audio.data,
            audio.sample_rate,
            reference=ref_audio_data,
        )

        # 품질 점수
        quality_score = metrics.get_quality_score(results)

        # 결과 출력
        click.echo(f"\n품질 분석 결과: {audio_path}\n")
        click.echo(f"품질 점수: {quality_score:.2f} / 1.00")
        click.echo(f"\nRMS 에너지: {results['rms_energy']:.4f}")
        click.echo(f"Zero Crossing Rate: {results['zero_crossing_rate']:.4f}")
        click.echo(f"스펙트럼 중심: {results['spectral_centroid']:.1f} Hz")

        click.echo(f"\n클리핑:")
        click.echo(f"  - 클리핑 샘플: {results['clipping']['clipped_samples']}")
        click.echo(f"  - 클리핑 비율: {results['clipping']['clipping_ratio']:.2%}")
        click.echo(f"  - 클리핑 감지: {'예' if results['clipping']['is_clipped'] else '아니오'}")

        click.echo(f"\n무음:")
        click.echo(f"  - 무음 샘플: {results['silence']['silent_samples']}")
        click.echo(f"  - 무음 비율: {results['silence']['silence_ratio']:.2%}")
        click.echo(f"  - 무음 구간 수: {results['silence']['num_silent_intervals']}")

        # 참조 오디오와 비교
        if reference:
            click.echo(f"\n참조 오디오와 비교:")
            click.echo(f"  - SNR: {results['snr']:.2f} dB")
            click.echo(f"  - MSE: {results['mse']:.6f}")
            click.echo(f"  - 스펙트럼 거리: {results['spectral_distance']:.2f}")

        # JSON 저장 (옵션)
        if output:
            output_data = {
                **results,
                'quality_score': quality_score,
                'audio_path': str(audio_path),
                'reference_path': str(reference) if reference else None,
            }

            with open(output, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            click.echo(f"\n결과 저장: {output}")

    except Exception as e:
        logger.error(f"오류 발생: {str(e)}", exc_info=ctx.obj['debug'])
        click.echo(f"\n오류: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('target_path', type=click.Path(exists=True))
@click.argument('source_paths', nargs=-1, type=click.Path(exists=True), required=True)
@click.option('--algorithm', '-a', default='mfcc', help='유사도 알고리즘')
@click.option('--top-k', '-k', type=int, default=3, help='표시할 최대 매치 수')
@click.pass_context
def preview(ctx, target_path, source_paths, algorithm, top_k):
    """
    합성 미리보기 (실제 합성 없이 매치만 찾기).

    TARGET_PATH: 타겟 오디오 파일 경로

    SOURCE_PATHS: 소스 오디오 파일 경로들
    """
    logger = ctx.obj['logger']

    try:
        logger.info(f"미리보기: {target_path}")

        # 알고리즘 선택
        if algorithm == 'mfcc':
            sim_algo = MFCCSimilarity()
        elif algorithm == 'spectral':
            from algorithms.traditional.spectral import SpectralSimilarity
            sim_algo = SpectralSimilarity()
        elif algorithm == 'embedding':
            sim_algo = EmbeddingSimilarity(device='cpu')
        elif algorithm == 'hybrid':
            sim_algo = HybridSimilarity()
        else:
            raise ValueError(f"지원하지 않는 알고리즘: {algorithm}")

        # 타겟 로드
        target = AudioFile.load(target_path)

        click.echo(f"\n타겟: {target_path}")
        click.echo(f"길이: {len(target.data) / target.sample_rate:.2f}초\n")

        # 각 소스에서 매치 찾기
        all_matches = []

        for i, source_path in enumerate(source_paths, 1):
            click.echo(f"소스 {i}/{len(source_paths)}: {source_path}")

            source = AudioFile.load(source_path)

            matches = sim_algo.find_similar_segments(
                target.data, source.data,
                target.sample_rate, source.sample_rate,
                top_k=top_k,
            )

            for j, match in enumerate(matches, 1):
                click.echo(
                    f"  매치 {j}: 유사도={match.similarity:.3f}, "
                    f"위치={match.source_start:.2f}s~{match.source_end:.2f}s"
                )
                match.metadata = match.metadata or {}
                match.metadata['source_file'] = str(source_path)

            all_matches.extend(matches)

        # 전체 최고 매치
        if all_matches:
            all_matches.sort(key=lambda m: m.similarity, reverse=True)
            best = all_matches[0]

            click.echo(f"\n최고 매치:")
            click.echo(f"  파일: {best.metadata['source_file']}")
            click.echo(f"  유사도: {best.similarity:.3f}")
            click.echo(f"  위치: {best.source_start:.2f}s ~ {best.source_end:.2f}s")

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
