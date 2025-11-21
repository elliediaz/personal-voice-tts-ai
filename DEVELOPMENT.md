# 개발 가이드

이 문서는 Personal Voice TTS AI 프로젝트의 개발 과정과 진행 방법을 설명합니다.

## 개발 철학

1. **단계별 개발**: 프로젝트는 8개의 페이즈로 나뉘어 단계적으로 개발됩니다
2. **모듈화**: 각 컴포넌트는 독립적으로 작동하며 개별 테스트가 가능합니다
3. **테스트 주도**: 모든 기능은 단위 테스트를 포함해야 합니다
4. **문서화**: 코드는 자체 문서화되어야 하며, 모든 공개 API는 docstring을 포함합니다

## 개발 환경 설정

### 필수 요구사항

- Python 3.9 이상
- Git
- 가상환경 (venv 또는 conda)

### 초기 설정

```bash
# 저장소 클론
git clone <repository-url>
cd personal-voice-tts-ai

# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 개발 의존성 설치 (Phase 1 진행 시)
pip install -r requirements-dev.txt
```

## 개발 워크플로

### 1. 페이즈 선택

현재 프로젝트는 다음 페이즈로 구성됩니다:

- **Phase 1**: Foundation & Basic Audio Processing
- **Phase 2**: Traditional Similarity Detection
- **Phase 3**: AI-Based Similarity Detection
- **Phase 4**: Audio Synthesis Engine
- **Phase 5**: TTS Integration
- **Phase 6**: Batch Processing & Pipeline
- **Phase 7**: GUI Implementation
- **Phase 8**: Optimization & Documentation

### 2. 페이즈 프롬프트 사용

각 페이즈는 상세한 프롬프트를 가지고 있습니다:

- `CLAUDE.md`: 전체 페이즈 프롬프트 포함
- `PHASE1_PROMPT.md`: Phase 1 상세 가이드

개발 시작 시:
1. 해당 페이즈의 프롬프트를 읽습니다
2. 요구사항을 이해합니다
3. 프롬프트를 도구에 입력하여 개발을 시작합니다

### 3. 개발 진행

```bash
# 새 기능 브랜치 생성
git checkout -b feature/phase1-audio-io

# 개발 진행
# - 코드 작성
# - 테스트 작성
# - 로컬 테스트 실행

# 테스트 실행
pytest tests/

# 코드 스타일 검사 (추후)
# black .
# flake8 .

# 변경사항 커밋
git add .
git commit -m "기능: 오디오 I/O 모듈 구현"

# 브랜치 푸시
git push -u origin feature/phase1-audio-io
```

### 4. 테스트

모든 코드는 테스트를 포함해야 합니다:

```bash
# 전체 테스트 실행
pytest

# 특정 테스트 파일 실행
pytest tests/test_audio_io.py

# 커버리지 포함
pytest --cov=core --cov-report=html

# 특정 테스트만 실행
pytest tests/test_audio_io.py::test_load_wav_file
```

### 5. 커밋 메시지 규칙

한글로 작성하며, 다음 형식을 따릅니다:

```
<타입>: <제목>

<본문 (선택사항)>

<푸터 (선택사항)>
```

타입:
- `기능`: 새로운 기능 추가
- `수정`: 버그 수정
- `문서`: 문서 변경
- `스타일`: 코드 스타일 변경 (포맷팅 등)
- `리팩토링`: 코드 리팩토링
- `테스트`: 테스트 추가 또는 수정
- `빌드`: 빌드 시스템 변경
- `성능`: 성능 개선

예시:
```
기능: MFCC 기반 유사도 검출 알고리즘 구현

- MFCC 특징 추출 함수 추가
- 동적 시간 와핑(DTW) 거리 계산 구현
- 유사도 임계값 설정 기능 추가
- 단위 테스트 작성

Closes #15
```

### 6. 코드 스타일

#### Python 코드 스타일

- PEP 8 준수
- 변수/함수명: 영어 snake_case
- 클래스명: 영어 PascalCase
- 상수: 영어 UPPER_SNAKE_CASE
- 타입 힌트 사용
- Docstring: 한글 (Google 또는 NumPy 스타일)

예시:
```python
from typing import Optional, Tuple
import numpy as np

def load_audio_file(file_path: str, sample_rate: Optional[int] = None) -> Tuple[np.ndarray, int]:
    """
    오디오 파일을 로드합니다.

    Args:
        file_path: 로드할 오디오 파일의 경로
        sample_rate: 목표 샘플링 레이트 (None인 경우 원본 사용)

    Returns:
        오디오 데이터 배열과 샘플링 레이트의 튜플

    Raises:
        FileNotFoundError: 파일이 존재하지 않을 때
        ValueError: 지원하지 않는 파일 형식일 때
    """
    # 구현...
    pass
```

#### 주석 스타일

- 코드 주석: 한글
- TODO 주석: 한글
- 복잡한 로직 설명: 한글

```python
# 오디오 신호를 정규화하여 -1.0 ~ 1.0 범위로 조정
normalized_audio = audio / np.max(np.abs(audio))

# TODO: 멀티채널 오디오 지원 추가 필요
```

### 7. 디렉토리 구조 규칙

- `core/`: 핵심 기능 모듈
- `algorithms/`: 알고리즘 구현
- `cli/`: CLI 인터페이스
- `gui/`: GUI 구현
- `utils/`: 유틸리티 함수
- `config/`: 설정 파일
- `tests/`: 테스트 코드
- `docs/`: 문서
- `examples/`: 예제 코드

각 디렉토리는 `__init__.py`를 포함해야 합니다.

### 8. 설정 파일 관리

- 기본 설정: `config.default.yml` (git에 포함)
- 사용자 설정: `config.yml` (git에서 제외)
- 로컬 설정: `config.local.yml` (git에서 제외)

설정 파일 우선순위:
1. `config.local.yml`
2. `config.yml`
3. `config.default.yml`

## 페이즈별 개발 가이드

### Phase 1: 기초 구조

**목표**: 프로젝트 기본 구조 및 오디오 I/O 기능

**진행 방법**:
1. `PHASE1_PROMPT.md` 읽기
2. 프롬프트를 개발 도구에 입력
3. 디렉토리 구조 생성
4. 오디오 I/O 모듈 구현
5. 테스트 작성 및 실행
6. CLI 구현
7. 문서 작성
8. 커밋 및 푸시

**완료 기준**:
- [ ] 모든 테스트 통과
- [ ] CLI 명령어 동작 확인
- [ ] 문서 작성 완료
- [ ] 코드 리뷰 완료

### Phase 2~8

각 페이즈는 `CLAUDE.md`의 해당 섹션을 참조하여 진행합니다.

## 테스트 전략

### 단위 테스트

각 모듈은 독립적인 단위 테스트를 가져야 합니다:

```python
# tests/test_audio_io.py
import pytest
from core.audio.io import AudioFile

def test_load_wav_file():
    """WAV 파일 로딩 테스트"""
    audio = AudioFile.load("tests/fixtures/sample.wav")
    assert audio.sample_rate == 44100
    assert audio.channels == 2
    assert audio.duration > 0

def test_load_nonexistent_file():
    """존재하지 않는 파일 로딩 시 예외 발생 테스트"""
    with pytest.raises(FileNotFoundError):
        AudioFile.load("nonexistent.wav")
```

### 통합 테스트

여러 모듈이 함께 작동하는지 테스트:

```python
# tests/integration/test_similarity_pipeline.py
def test_full_similarity_pipeline():
    """전체 유사도 검출 파이프라인 테스트"""
    # 타겟 로딩
    target = AudioFile.load("tests/fixtures/target.wav")

    # 소스 로딩
    source = AudioFile.load("tests/fixtures/source.wav")

    # 유사도 검출
    matcher = MFCCSimilarity()
    matches = matcher.find_similar_segments(target, source)

    # 검증
    assert len(matches) > 0
    assert matches[0].similarity > 0.5
```

### 성능 테스트

```python
# tests/performance/test_performance.py
import time

def test_similarity_performance():
    """유사도 검출 성능 테스트"""
    target = AudioFile.load("tests/fixtures/long_audio.wav")
    source = AudioFile.load("tests/fixtures/source.wav")

    start_time = time.time()
    matcher = MFCCSimilarity()
    matches = matcher.find_similar_segments(target, source)
    elapsed_time = time.time() - start_time

    # 10초 이내에 완료되어야 함
    assert elapsed_time < 10.0
```

## 문서화

### 코드 문서화

모든 공개 함수/클래스는 docstring을 포함해야 합니다:

```python
class AudioFile:
    """
    오디오 파일을 표현하는 클래스.

    이 클래스는 다양한 형식의 오디오 파일을 로드하고 저장하며,
    기본적인 메타데이터를 제공합니다.

    Attributes:
        data: 오디오 데이터 (numpy 배열)
        sample_rate: 샘플링 레이트 (Hz)
        channels: 채널 수
        duration: 오디오 길이 (초)

    Examples:
        >>> audio = AudioFile.load("sample.wav")
        >>> print(f"Duration: {audio.duration}s")
        >>> audio.save("output.mp3")
    """
    pass
```

### API 문서

각 페이즈 완료 후 API 문서를 업데이트합니다:

- 모듈별 README.md
- API 레퍼런스 (Sphinx 또는 MkDocs 사용)
- 사용 예제

### 사용자 문서

- README.md: 프로젝트 개요 및 빠른 시작
- INSTALL.md: 설치 가이드
- USAGE.md: 사용 방법
- DEVELOPMENT.md: 개발 가이드 (이 문서)
- CONTRIBUTING.md: 기여 가이드

## 의존성 관리

### requirements.txt 구조

```
requirements.txt           # 기본 실행 의존성
requirements-dev.txt      # 개발 의존성
requirements-ai.txt       # AI 기능 의존성 (선택)
requirements-gui.txt      # GUI 의존성 (선택)
```

### 의존성 추가

새로운 의존성 추가 시:
1. 적절한 requirements 파일에 추가
2. 버전 명시 (호환성 보장)
3. 주석으로 용도 설명

```txt
# requirements.txt
numpy>=1.21.0,<2.0.0      # 수치 연산
librosa>=0.9.0,<1.0.0     # 오디오 분석
```

## 디버깅

### 로깅 사용

print 대신 logging 사용:

```python
import logging

logger = logging.getLogger(__name__)

def process_audio(audio_path: str):
    logger.info(f"오디오 파일 처리 시작: {audio_path}")
    try:
        # 처리 로직
        logger.debug("MFCC 추출 중...")
        pass
    except Exception as e:
        logger.error(f"오디오 처리 실패: {e}", exc_info=True)
        raise
    finally:
        logger.info("오디오 파일 처리 완료")
```

### 디버그 모드

```bash
# 디버그 모드로 실행
python -m cli.basic info audio.wav --debug

# 또는 환경변수 사용
export DEBUG=1
python -m cli.basic info audio.wav
```

## 성능 최적화

### 프로파일링

```python
import cProfile
import pstats

# 프로파일링 실행
profiler = cProfile.Profile()
profiler.enable()

# 측정할 코드
process_audio("long_audio.wav")

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # 상위 20개 출력
```

### 메모리 프로파일링

```bash
# memory_profiler 사용
pip install memory_profiler
python -m memory_profiler cli/basic.py
```

## 배포

### 패키지 빌드

```bash
# 패키지 빌드
python setup.py sdist bdist_wheel

# 로컬 설치 테스트
pip install dist/personal_voice_tts_ai-0.1.0-py3-none-any.whl
```

### 버전 관리

Semantic Versioning (SemVer) 사용:
- MAJOR.MINOR.PATCH
- 예: 1.2.3

## 참고 자료

- [Python Style Guide (PEP 8)](https://pep8.org/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [pytest Documentation](https://docs.pytest.org/)
- [librosa Documentation](https://librosa.org/doc/latest/)

## 문제 해결

### 자주 발생하는 문제

1. **오디오 파일 로딩 실패**
   - 파일 형식 확인
   - 코덱 설치 확인 (ffmpeg)
   - 파일 권한 확인

2. **메모리 부족**
   - 배치 크기 줄이기
   - 스트리밍 처리 사용
   - 캐시 정리

3. **테스트 실패**
   - 의존성 버전 확인
   - 테스트 픽스처 파일 확인
   - 격리된 환경에서 재실행

## 연락처

문제나 질문이 있을 경우 GitHub Issues를 통해 문의해주세요.
