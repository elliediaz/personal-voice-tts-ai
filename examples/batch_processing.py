"""
배치 처리 예제

여러 텍스트를 일괄적으로 TTS-to-Collage 처리합니다.
"""

from pathlib import Path
from core.batch.processor import BatchProcessor
from core.tts.backends import GTTSBackend
from core.tts.pipeline import TTSPipeline
from algorithms.traditional.mfcc import MFCCSimilarity


def main():
    """메인 함수"""
    print("=== 배치 처리 예제 ===\n")

    # 설정
    texts = [
        "첫 번째 문장입니다.",
        "두 번째 문장입니다.",
        "세 번째 문장입니다.",
        "네 번째 문장입니다.",
        "다섯 번째 문장입니다.",
    ]

    source_files = [
        Path("voice1.wav"),
        Path("voice2.wav"),
    ]

    output_dir = Path("batch_outputs")
    output_dir.mkdir(exist_ok=True)

    # 소스 파일 확인
    existing_sources = [f for f in source_files if f.exists()]
    if not existing_sources:
        print("오류: 소스 오디오 파일을 찾을 수 없습니다.")
        return

    print(f"처리할 텍스트 수: {len(texts)}")
    print(f"소스 파일 수: {len(existing_sources)}")
    print(f"출력 디렉토리: {output_dir}\n")

    # TTS 파이프라인 생성
    print("TTS 파이프라인 초기화...")
    tts_backend = GTTSBackend(language="ko")
    similarity_algorithm = MFCCSimilarity()
    pipeline = TTSPipeline(
        tts_engine=tts_backend,
        similarity_algorithm=similarity_algorithm,
    )

    # 배치 프로세서 생성
    print("배치 프로세서 생성 (워커: 4)")
    processor = BatchProcessor(
        max_workers=4,
        use_processes=False,
        continue_on_error=True,
        show_progress=True,
    )

    # 작업 추가
    print(f"\n{len(texts)}개 작업 추가 중...")
    for i, text in enumerate(texts, 1):
        output_path = output_dir / f"output_{i:03d}.wav"
        processor.add_job(
            job_id=f"tts_collage_{i}",
            func=pipeline.synthesize_collage,
            kwargs={
                "text": text,
                "source_files": existing_sources,
                "output_path": output_path,
            },
            priority=0,
        )

    # 배치 처리 실행
    print("\n배치 처리 시작...\n")

    try:
        summary = processor.process_all()

        print("\n\n=== 배치 처리 완료 ===")
        print(f"전체 작업: {summary['total_count']}")
        print(f"성공: {summary['success_count']}")
        print(f"실패: {summary['error_count']}")
        print(f"성공률: {summary['success_rate']:.1f}%")
        print(f"소요 시간: {summary['total_time']:.2f}초")
        print(f"처리 속도: {summary['jobs_per_second']:.2f} jobs/sec")
        print(f"\n출력 파일 위치: {output_dir}")

    except Exception as e:
        print(f"\n오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
