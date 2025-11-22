"""
AI Similarity CLI Module

AI 기반 유사도 검출을 위한 CLI 명령어를 제공합니다.
"""

import sys
import json
from pathlib import Path

import click

from core.audio.io import AudioFile
from algorithms.ai_based.embedding_matcher import EmbeddingSimilarity
from algorithms.ai_based.hybrid import HybridSimilarity
from core.ai.model_manager import ModelManager
from config import get_config
from utils.logging import setup_logger

logger = None


def init_logger(debug: bool = False):
    """로거를 초기화합니다."""
    global logger
    config = get_config()

    level = "DEBUG" if debug else config.logging.level

    logger = setup_logger(
        "ai_similarity",
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
    Personal Voice TTS AI - AI 기반 유사도 검출 CLI 도구

    딥러닝 모델을 사용한 고급 오디오 유사도 분석 도구
    """
    ctx.ensure_object(dict)
    ctx.obj['logger'] = init_logger(debug)
    ctx.obj['debug'] = debug


@cli.command()
@click.argument('target_path', type=click.Path(exists=True))
@click.argument('source_path', type=click.Path(exists=True))
@click.option('--model', '-m', default='wav2vec2-base', help='사용할 모델 (wav2vec2-base, wav2vec2-large, hubert-base, hubert-large)')
@click.option('--pooling', '-p', default='mean', help='풀링 방법 (mean, max, attention)')
@click.option('--top-k', '-k', type=int, default=10, help='반환할 최대 매치 수')
@click.option('--output', '-o', type=click.Path(), help='결과 저장 경로 (JSON)')
@click.option('--metadata', type=click.Path(), help='메타데이터 저장 경로 (JSON)')
@click.pass_context
def find(ctx, target_path, source_path, model, pooling, top_k, output, metadata):
    """
    AI 모델을 사용하여 유사한 세그먼트를 찾습니다.

    TARGET_PATH: 타겟 오디오 파일 경로
    SOURCE_PATH: 소스 오디오 파일 경로
    """
    logger = ctx.obj['logger']

    try:
        logger.info(f"AI 기반 유사 세그먼트 검색 시작...")
        logger.info(f"타겟: {target_path}")
        logger.info(f"소스: {source_path}")
        logger.info(f"모델: {model}, 풀링: {pooling}")

        # 오디오 로드
        target = AudioFile.load(target_path)
        source = AudioFile.load(source_path)

        # AI 알고리즘 생성
        algo = EmbeddingSimilarity(
            model_name=model,
            pooling=pooling,
        )

        # 유사 세그먼트 찾기
        matches = algo.find_similar_segments(
            target.data,
            source.data,
            target.sample_rate,
            source.sample_rate,
            top_k=top_k,
        )

        # 결과 출력
        click.echo(f"\n{len(matches)}개의 유사 세그먼트 발견:\n")

        for i, match in enumerate(matches, 1):
            click.echo(f"{i}. 유사도: {match.similarity:.3f}, 신뢰도: {match.confidence:.3f}")
            click.echo(f"   소스 위치: {match.source_start:.2f}s ~ {match.source_end:.2f}s")
            click.echo(f"   길이: {match.source_duration:.2f}s")
            if match.metadata:
                click.echo(f"   모델: {match.metadata.get('model', 'N/A')}")
            click.echo()

        # JSON 저장 (옵션)
        if output:
            result_data = {
                'target': str(target_path),
                'source': str(source_path),
                'model': model,
                'pooling': pooling,
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

        # 메타데이터 저장 (옵션)
        if metadata and matches:
            from core.ai.metadata import AIMetadata

            similarities = [m.similarity for m in matches]
            ai_metadata = algo.create_metadata(
                inference_time=0.0,  # 실제로는 측정된 시간 사용
                num_matches=len(matches),
                similarities=similarities,
            )

            ai_metadata.save(metadata)
            logger.info(f"메타데이터 저장 완료: {metadata}")
            click.echo(f"메타데이터 저장: {metadata}")

    except Exception as e:
        logger.error(f"오류 발생: {str(e)}", exc_info=ctx.obj['debug'])
        sys.exit(1)


@cli.command()
@click.argument('target_path', type=click.Path(exists=True))
@click.argument('source_path', type=click.Path(exists=True))
@click.option('--model', '-m', default='wav2vec2-base', help='AI 모델')
@click.option('--traditional', '-t', default='mfcc', help='전통적 알고리즘 (mfcc, spectral, energy)')
@click.option('--ai-weight', type=float, default=0.6, help='AI 가중치')
@click.option('--top-k', '-k', type=int, default=10, help='반환할 최대 매치 수')
@click.option('--output', '-o', type=click.Path(), help='결과 저장 경로 (JSON)')
@click.pass_context
def hybrid(ctx, target_path, source_path, model, traditional, ai_weight, top_k, output):
    """
    하이브리드 방식으로 유사한 세그먼트를 찾습니다.

    전통적 알고리즘과 AI 알고리즘을 결합합니다.

    TARGET_PATH: 타겟 오디오 파일 경로
    SOURCE_PATH: 소스 오디오 파일 경로
    """
    logger = ctx.obj['logger']

    try:
        logger.info(f"하이브리드 검색 시작...")
        logger.info(f"AI 모델: {model}, 전통적: {traditional}, AI 가중치: {ai_weight}")

        # 오디오 로드
        target = AudioFile.load(target_path)
        source = AudioFile.load(source_path)

        # 전통적 알고리즘 선택
        if traditional == 'mfcc':
            from algorithms.traditional.mfcc import MFCCSimilarity
            trad_algo = MFCCSimilarity()
        elif traditional == 'spectral':
            from algorithms.traditional.spectral import SpectralSimilarity
            trad_algo = SpectralSimilarity()
        elif traditional == 'energy':
            from algorithms.traditional.energy import EnergySimilarity
            trad_algo = EnergySimilarity()
        else:
            raise ValueError(f"지원하지 않는 전통적 알고리즘: {traditional}")

        # AI 알고리즘 생성
        ai_algo = EmbeddingSimilarity(model_name=model)

        # 하이브리드 알고리즘 생성
        hybrid_algo = HybridSimilarity(
            traditional_algorithm=trad_algo,
            ai_algorithm=ai_algo,
            traditional_weight=1.0 - ai_weight,
            ai_weight=ai_weight,
        )

        # 유사 세그먼트 찾기
        matches = hybrid_algo.find_similar_segments(
            target.data,
            source.data,
            target.sample_rate,
            source.sample_rate,
            top_k=top_k,
        )

        # 결과 출력
        click.echo(f"\n{len(matches)}개의 유사 세그먼트 발견 (하이브리드):\n")

        for i, match in enumerate(matches, 1):
            click.echo(f"{i}. 유사도: {match.similarity:.3f}")
            click.echo(f"   소스 위치: {match.source_start:.2f}s ~ {match.source_end:.2f}s")

            if match.metadata:
                trad_score = match.metadata.get('traditional_score', 'N/A')
                ai_score = match.metadata.get('ai_score', 'N/A')
                if trad_score != 'N/A' and ai_score != 'N/A':
                    click.echo(f"   전통적 점수: {trad_score:.3f}, AI 점수: {ai_score:.3f}")

            click.echo()

        # JSON 저장 (옵션)
        if output:
            result_data = {
                'target': str(target_path),
                'source': str(source_path),
                'method': 'hybrid',
                'ai_model': model,
                'traditional_algorithm': traditional,
                'ai_weight': ai_weight,
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
def list_models():
    """사용 가능한 AI 모델 목록을 나열합니다."""
    manager = ModelManager()
    models = manager.list_available_models()

    click.echo("\n사용 가능한 AI 모델:\n")
    for model_name in models:
        info = manager.get_model_info(model_name)
        click.echo(f"  - {model_name}")
        click.echo(f"    HuggingFace ID: {info['huggingface_id']}")
        click.echo(f"    타입: {info['type']}")
        click.echo()


@cli.command()
@click.argument('model_name')
def download_model(model_name):
    """
    AI 모델을 미리 다운로드합니다.

    MODEL_NAME: 모델 이름 (예: wav2vec2-base)
    """
    try:
        click.echo(f"모델 다운로드 중: {model_name}...")

        manager = ModelManager()
        model, processor = manager.load_model(model_name)

        click.echo(f"모델 다운로드 완료: {model_name}")
        click.echo(f"캐시 디렉토리: {manager.get_cache_dir()}")

    except Exception as e:
        click.echo(f"오류 발생: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('audio_path', type=click.Path(exists=True))
@click.option('--model', '-m', default='wav2vec2-base', help='사용할 모델')
@click.option('--output', '-o', type=click.Path(), help='임베딩 저장 경로 (.npy)')
@click.pass_context
def extract_embedding(ctx, audio_path, model, output):
    """
    오디오 파일에서 임베딩을 추출합니다.

    AUDIO_PATH: 오디오 파일 경로
    """
    logger = ctx.obj['logger']

    try:
        logger.info(f"임베딩 추출 중: {audio_path}")

        # 오디오 로드
        audio = AudioFile.load(audio_path)

        # 임베딩 추출기 생성
        from algorithms.ai_based.embeddings import EmbeddingExtractor

        extractor = EmbeddingExtractor(model_name=model)

        # 임베딩 추출
        embedding, inference_time = extractor.extract(
            audio.data, audio.sample_rate, return_time=True
        )

        click.echo(f"\n임베딩 추출 완료:")
        click.echo(f"  모델: {model}")
        click.echo(f"  임베딩 차원: {len(embedding)}")
        click.echo(f"  추론 시간: {inference_time:.3f}초")

        # 저장 (옵션)
        if output:
            import numpy as np

            output_path = Path(output)
            np.save(output_path, embedding)
            click.echo(f"\n임베딩 저장: {output_path}")

    except Exception as e:
        logger.error(f"오류 발생: {str(e)}", exc_info=ctx.obj['debug'])
        sys.exit(1)


def main():
    """CLI 진입점"""
    cli(obj={})


if __name__ == '__main__':
    main()


__all__ = ["cli", "main"]
