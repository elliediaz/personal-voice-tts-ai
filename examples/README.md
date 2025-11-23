# 예제 모음

Personal Voice TTS AI의 다양한 사용 예제입니다.

## 예제 목록

### 1. basic_synthesis.py
기본 오디오 합성 예제입니다. 타겟 오디오와 소스 오디오를 사용하여 콜라주를 생성합니다.

**실행 방법:**
```bash
python examples/basic_synthesis.py
```

**필요한 파일:**
- `target.wav`: 타겟 오디오 파일
- `source1.wav`, `source2.wav`, `source3.wav`: 소스 오디오 파일

### 2. tts_collage.py
TTS-to-Collage 예제입니다. 텍스트를 TTS로 변환한 후 소스 오디오로 콜라주합니다.

**실행 방법:**
```bash
python examples/tts_collage.py
```

**필요한 파일:**
- `voice1.wav`, `voice2.wav`, `voice3.wav`: 소스 음성 파일

### 3. batch_processing.py
배치 처리 예제입니다. 여러 텍스트를 일괄적으로 처리합니다.

**실행 방법:**
```bash
python examples/batch_processing.py
```

**필요한 파일:**
- `voice1.wav`, `voice2.wav`: 소스 음성 파일

## 테스트 오디오 파일 준비

예제를 실행하기 위해서는 테스트 오디오 파일이 필요합니다.

### 옵션 1: 직접 녹음
- 마이크로 5-10초 분량의 음성을 녹음하세요
- WAV 포맷으로 저장하세요
- 파일명을 예제에 맞게 변경하세요 (예: `voice1.wav`)

### 옵션 2: TTS로 생성
```python
from core.tts.backends import GTTSBackend

tts = GTTSBackend(language="ko")
tts.synthesize("테스트 음성입니다.", output_path="voice1.wav")
```

### 옵션 3: 샘플 오디오 다운로드
다양한 무료 오디오 샘플:
- [Freesound](https://freesound.org/)
- [Free Music Archive](https://freemusicarchive.org/)

## 문제 해결

### ImportError
필요한 패키지가 설치되지 않은 경우:
```bash
pip install personal-voice-tts-ai[all]
```

### 파일을 찾을 수 없음
- 예제 스크립트와 같은 디렉토리에 오디오 파일을 배치하세요
- 또는 스크립트에서 파일 경로를 수정하세요

### 처리 속도가 느림
- GPU 사용을 고려하세요 (AI 알고리즘 사용 시)
- 배치 처리 시 `max_workers`를 조정하세요
- 더 빠른 알고리즘 (예: MFCC)을 사용하세요

## 더 많은 예제

추가 예제는 [문서](../docs/)를 참조하세요.
