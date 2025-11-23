"""
기본 오디오 합성 예제

타겟 오디오와 소스 오디오를 사용하여 콜라주 합성을 수행합니다.
"""

from pathlib import Path
from core.synthesis.engine import CollageEngine
from algorithms.traditional.mfcc import MFCCSimilarity


def main():
    """메인 함수"""
    print("=== 기본 오디오 합성 예제 ===\n")

    # 파일 경로 설정
    target_file = Path("target.wav")
    source_files = [
        Path("source1.wav"),
        Path("source2.wav"),
        Path("source3.wav"),
    ]
    output_file = Path("output.wav")

    # 파일 존재 확인
    if not target_file.exists():
        print(f"오류: 타겟 파일을 찾을 수 없습니다: {target_file}")
        print("타겟 오디오 파일(target.wav)을 준비해주세요.")
        return

    for source_file in source_files:
        if not source_file.exists():
            print(f"경고: 소스 파일을 찾을 수 없습니다: {source_file}")

    # 유사도 알고리즘 선택
    print("유사도 알고리즘 초기화: MFCC")
    similarity_algorithm = MFCCSimilarity(
        n_mfcc=13,
        threshold=0.5,
    )

    # 합성 엔진 생성
    print("합성 엔진 생성")
    engine = CollageEngine(
        similarity_algorithm=similarity_algorithm,
        crossfade_duration=0.05,
        blend_algorithm="equal_power",
    )

    # 합성 실행
    print(f"\n타겟: {target_file}")
    print(f"소스: {', '.join(str(f) for f in source_files)}")
    print(f"출력: {output_file}\n")
    print("합성 시작...")

    try:
        metadata = engine.synthesize_from_file(
            target_file=target_file,
            source_files=source_files,
            output_path=output_file,
            top_k=1,
            adjust_pitch=True,
            adjust_tempo=True,
            match_prosody=True,
            enhance_quality=True,
        )

        print("\n합성 완료!")
        print(f"출력 파일: {output_file}")
        print(f"\n메타데이터:")
        print(f"  - 타겟 길이: {metadata.get('target_duration', 'N/A')}초")
        print(f"  - 출력 길이: {metadata.get('output_duration', 'N/A')}초")
        print(f"  - 사용된 세그먼트 수: {metadata.get('segment_count', 'N/A')}")

    except Exception as e:
        print(f"\n오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
