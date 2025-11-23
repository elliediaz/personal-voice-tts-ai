"""
TTS-to-Collage 예제

텍스트를 TTS로 변환한 후 소스 오디오로 콜라주합니다.
"""

from pathlib import Path
from core.tts.backends import GTTSBackend
from core.tts.pipeline import TTSPipeline
from algorithms.traditional.mfcc import MFCCSimilarity


def main():
    """메인 함수"""
    print("=== TTS-to-Collage 예제 ===\n")

    # 설정
    text = "안녕하세요. Personal Voice TTS AI입니다. 텍스트를 음성으로 변환하고 콜라주합니다."
    source_files = [
        Path("voice1.wav"),
        Path("voice2.wav"),
        Path("voice3.wav"),
    ]
    output_file = Path("tts_collage_output.wav")

    # 소스 파일 확인
    existing_sources = [f for f in source_files if f.exists()]
    if not existing_sources:
        print("오류: 소스 오디오 파일을 찾을 수 없습니다.")
        print("소스 파일(voice1.wav, voice2.wav 등)을 준비해주세요.")
        return

    print(f"텍스트: {text}")
    print(f"소스 파일: {len(existing_sources)}개")
    print(f"출력: {output_file}\n")

    # TTS 백엔드 생성
    print("TTS 백엔드 초기화: Google TTS (Korean)")
    tts_backend = GTTSBackend(
        language="ko",
        tld="com",
        slow=False,
    )

    # 유사도 알고리즘
    print("유사도 알고리즘 초기화: MFCC")
    similarity_algorithm = MFCCSimilarity(threshold=0.5)

    # TTS 파이프라인 생성
    print("TTS 파이프라인 생성")
    pipeline = TTSPipeline(
        tts_engine=tts_backend,
        similarity_algorithm=similarity_algorithm,
    )

    # 처리 시작
    print("\nTTS-to-Collage 처리 시작...\n")

    try:
        metadata = pipeline.synthesize_collage(
            text=text,
            source_files=existing_sources,
            output_path=output_file,
        )

        print("\n처리 완료!")
        print(f"출력 파일: {output_file}")
        print(f"\n메타데이터:")
        print(f"  - 입력 텍스트 길이: {len(text)}자")
        print(f"  - TTS 오디오 길이: {metadata.get('tts_duration', 'N/A')}초")
        print(f"  - 최종 출력 길이: {metadata.get('output_duration', 'N/A')}초")

    except Exception as e:
        print(f"\n오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
