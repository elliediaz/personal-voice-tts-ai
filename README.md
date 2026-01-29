# Personal Voice TTS AI

음성 콜라주 및 합성 기반의 고급 TTS 시스템

## 프로젝트 개요

이 프로젝트는 소스 오디오 파일들을 분석하여 타겟 음성과 유사한 구간을 찾아내고, 이를 지능적으로 콜라주하여 새로운 음성을 합성하는 시스템입니다. 전통적인 음성 분석 방법부터 최신 AI 기반 기법까지 다양한 알고리즘을 제공하며, TTS 기능을 통해 텍스트로부터 직접 음성을 생성할 수 있습니다.

## 주요 기능

### 1. 다양한 유사도 검출 알고리즘
- **전통적인 방법**: MFCC, 스펙트럼 분석, 에너지 기반 매칭
- **AI 기반 방법**: Wav2Vec2, HuBERT, 딥러닝 임베딩
- **하이브리드 방법**: 전통적 방법과 AI 방법의 결합
- **랜덤 매칭**: 베이스라인 비교용

### 2. 고급 오디오 합성
- 세그먼트 추출 및 정렬
- 크로스페이드 및 블렌딩
- 피치 및 템포 조정
- 프로소디 매칭
- 품질 향상 알고리즘

### 3. TTS 통합
- 다양한 TTS 백엔드 지원 (Google TTS, Coqui TTS, Bark 등)
- 텍스트 전처리 및 정규화
- 음성 커스터마이징
- 텍스트 → TTS → 콜라주 전체 워크플로

### 4. 전문적인 시각화
- 파형 및 스펙트로그램 표시
- 유사도 매트릭스 히트맵
- 주파수 분석 차트
- 품질 메트릭 대시보드

### 5. 배치 처리
- 다중 파일 처리
- 병렬 처리 지원
- 진행 상황 추적
- 오류 처리 및 복구

### 6. 사용자 친화적 GUI
- 직관적인 인터페이스
- 실시간 오디오 재생 및 시각화
- 파라미터 조정 패널
- 배치 작업 관리

### 7. 웹 서비스 API
- FastAPI 기반 RESTful API
- 오디오 분석 및 텍스트 전처리 엔드포인트
- 파일 업로드/다운로드 지원
- 웹 기반 사용자 인터페이스

## 시스템 요구사항

- Python 3.9 이상
- 4GB 이상의 RAM (AI 모델 사용 시 8GB 권장)
- CUDA 지원 GPU (선택사항, AI 기반 분석 가속화)

## 설치 방법

### 기본 설치

```bash
# 저장소 클론
git clone https://github.com/yourusername/personal-voice-tts-ai.git
cd personal-voice-tts-ai

# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 선택적 의존성

```bash
# AI 기반 분석을 위한 추가 패키지
pip install -r requirements-ai.txt

# GUI를 위한 추가 패키지
pip install -r requirements-gui.txt
```

## 빠른 시작

### 1. 기본 오디오 분석

```bash
# 오디오 파일 정보 출력
python -m cli.basic info path/to/audio.wav

# 스펙트로그램 생성
python -m cli.basic spectrogram path/to/audio.wav --output spectrogram.png
```

### 2. 유사도 검색

```bash
# 전통적인 방법으로 유사 구간 찾기
python -m cli.similarity find \
  --target path/to/target.wav \
  --source path/to/source.wav \
  --algorithm mfcc \
  --threshold 0.8

# AI 기반 방법으로 유사 구간 찾기
python -m cli.ai_similarity find \
  --target path/to/target.wav \
  --source path/to/source.wav \
  --model wav2vec2
```

### 3. 음성 합성

```bash
# 타겟 오디오를 소스 파일들로부터 합성
python -m cli.synthesize \
  --target path/to/target.wav \
  --sources path/to/source1.wav path/to/source2.wav \
  --output synthesized.wav \
  --algorithm hybrid
```

### 4. TTS 워크플로

```bash
# 텍스트로부터 콜라주 음성 생성
python -m cli.tts collage \
  --text "안녕하세요, 반갑습니다" \
  --sources path/to/source_voices/ \
  --output output.wav \
  --backend coqui
```

### 5. 배치 처리

```bash
# 배치 작업 제출
python -m cli.batch submit \
  --workflow tts_collage \
  --input texts.txt \
  --sources path/to/voices/ \
  --output-dir outputs/

# 작업 진행 상황 모니터링
python -m cli.batch monitor
```

### 6. GUI 실행

```bash
# GUI 애플리케이션 시작
python -m gui.app
```

### 7. 웹 서비스 실행

```bash
# 실행 스크립트 사용 (권장)
./run.sh              # Linux/macOS
run.bat               # Windows
python run.py         # 크로스플랫폼

# 또는 직접 실행
python -m uvicorn web.app:app --host 0.0.0.0 --port 8000 --reload

# 브라우저에서 접속: http://localhost:8000
```

## 실행 스크립트 사용법

프로젝트는 크로스플랫폼 실행 스크립트를 제공합니다. 모든 스크립트는 대화형 메뉴, 색상 출력, 자동 가상환경 감지를 지원합니다.

### 대화형 메뉴 모드

```bash
# 인자 없이 실행하면 대화형 메뉴 표시
./run.sh              # Linux/macOS
run.bat               # Windows
```

### 명령어 직접 실행

```bash
# Linux/macOS
./run.sh web                       # 웹 서버 실행 (기본 포트 8000)
./run.sh web --port 3000           # 포트 3000으로 웹 서버 실행
./run.sh gui                       # GUI 애플리케이션 실행
./run.sh cli basic info audio.wav  # CLI 오디오 정보 조회
./run.sh test -v                   # 상세 테스트 실행
./run.sh test -c                   # 커버리지 테스트 실행
./run.sh install all               # 모든 의존성 설치
./run.sh clean                     # 캐시 및 빌드 파일 정리

# Windows
run.bat web
run.bat web --port 3000
run.bat gui
run.bat cli basic info audio.wav
run.bat test -v
run.bat install all
run.bat clean

# Python (모든 플랫폼)
python run.py web --port 3000
python run.py cli basic info audio.wav
python run.py test
python run.py install --extras all
```

### 환경변수

```bash
# Linux/macOS
PVTTS_PORT=3000 ./run.sh web       # 환경변수로 포트 설정
PVTTS_DEBUG=1 ./run.sh web         # 디버그 모드 활성화

# Windows
set PVTTS_PORT=3000
run.bat web
```

| 환경변수 | 설명 | 기본값 |
|---------|------|--------|
| `PVTTS_HOST` | 웹 서버 호스트 | 0.0.0.0 |
| `PVTTS_PORT` | 웹 서버 포트 | 8000 |
| `PVTTS_DEBUG` | 디버그 모드 (1로 활성화) | 0 |

## 프로젝트 구조

```
personal-voice-tts-ai/
├── core/                    # 핵심 모듈
│   ├── audio/              # 오디오 처리
│   ├── similarity/         # 유사도 검출
│   ├── synthesis/          # 오디오 합성
│   ├── tts/                # TTS 통합
│   ├── ai/                 # AI 모델 관리
│   └── batch/              # 배치 처리
├── algorithms/             # 유사도 알고리즘 구현
│   ├── traditional/        # 전통적 방법
│   ├── ai_based/          # AI 기반 방법
│   └── random/            # 랜덤 매칭
├── web/                    # 웹 서비스
│   ├── static/            # 정적 파일 (CSS, JS)
│   └── templates/         # HTML 템플릿
├── utils/                  # 유틸리티 함수
├── gui/                    # GUI 구현
│   ├── widgets/           # UI 위젯
│   ├── panels/            # UI 패널
│   └── dialogs/           # 대화상자
├── cli/                    # CLI 인터페이스
├── config/                 # 설정 파일
├── tests/                  # 테스트 스위트
├── docs/                   # 문서
├── examples/              # 예제 및 튜토리얼
├── run.sh                 # 실행 스크립트 (Linux/macOS)
├── run.bat                # 실행 스크립트 (Windows)
└── run.py                 # 실행 스크립트 (크로스플랫폼)
```

## 설정

프로젝트의 동작은 `config/` 디렉토리의 YAML 파일을 통해 커스터마이징할 수 있습니다:

- `config.default.yml`: 기본 설정
- `similarity.yml`: 유사도 알고리즘 파라미터
- `synthesis.yml`: 합성 엔진 설정
- `tts.yml`: TTS 백엔드 설정
- `batch.yml`: 배치 처리 설정
- `gui.yml`: GUI 환경설정

설정을 수정하려면 `config.yml` 파일을 생성하여 기본값을 오버라이드하세요.

## 고급 사용법

### 알고리즘 파라미터 조정

```python
from core.similarity.manager import SimilarityManager
from algorithms.traditional.mfcc import MFCCSimilarity

# MFCC 알고리즘 설정
mfcc = MFCCSimilarity(
    n_mfcc=20,              # MFCC 계수 개수
    n_fft=2048,             # FFT 윈도우 크기
    hop_length=512,         # 홉 길이
    window='hamming',       # 윈도우 함수
    similarity_threshold=0.8 # 유사도 임계값
)

# 유사 구간 검색
matches = mfcc.find_similar_segments(target_audio, source_audio)
```

### 커스텀 워크플로 정의

`config/workflows/custom.yml`:

```yaml
name: 커스텀 음성 합성
stages:
  - name: 전처리
    module: core.audio.preprocessing
    params:
      normalize: true
      denoise: true

  - name: 유사도 검출
    module: algorithms.ai_based.hybrid
    params:
      models: [wav2vec2, mfcc]
      weights: [0.7, 0.3]

  - name: 합성
    module: core.synthesis.engine
    params:
      blend_algorithm: equal_power
      crossfade_duration: 0.05

  - name: 품질 향상
    module: core.synthesis.enhancement
    params:
      noise_reduction: true
      spectral_smoothing: true
```

## 개발 로드맵

- [x] Phase 1: 기본 프로젝트 구조 및 오디오 처리
- [x] Phase 2: 전통적인 유사도 검출
- [x] Phase 3: AI 기반 유사도 검출
- [x] Phase 4: 오디오 합성 엔진
- [x] Phase 5: TTS 통합
- [x] Phase 6: 배치 처리
- [x] Phase 7: GUI 구현
- [x] Phase 8: 최적화 및 문서화

## 기여 방법

기여를 환영합니다! 다음 절차를 따라주세요:

1. 이슈를 생성하여 버그나 기능 제안을 논의합니다
2. 프로젝트를 포크합니다
3. 기능 브랜치를 생성합니다 (`git checkout -b feature/amazing-feature`)
4. 변경사항을 커밋합니다 (`git commit -m '기능: 놀라운 기능 추가'`)
5. 브랜치에 푸시합니다 (`git push origin feature/amazing-feature`)
6. Pull Request를 생성합니다

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 문의

프로젝트 관련 문의사항이나 버그 리포트는 GitHub Issues를 통해 제출해주세요.

## 감사의 글

이 프로젝트는 다음 오픈소스 프로젝트들을 활용합니다:
- librosa: 오디오 분석
- PyTorch & Transformers: AI 모델
- Coqui TTS: 신경망 기반 TTS
- 그 외 많은 오픈소스 커뮤니티의 기여

## 변경 이력

### v0.9.0 (현재 버전)
- 향상된 실행 스크립트
  - 대화형 메뉴 시스템 (번호 선택 방식)
  - ASCII 아트 배너 및 색상 출력
  - 자동 가상환경 감지 및 활성화
  - Python 버전 검증 (3.9+ 필수)
  - 환경변수 지원 (PVTTS_HOST, PVTTS_PORT, PVTTS_DEBUG)
  - CLI 서브메뉴, 테스트 옵션 메뉴, 설치 옵션 메뉴
  - 캐시 및 빌드 파일 정리 기능
  - 시그널 트랩 (Linux/macOS)
- 버전 정보 통일 (0.9.0)
- 웹 서비스 및 크로스플랫폼 지원
  - FastAPI 기반 웹 API 구현
  - RESTful 엔드포인트 (오디오 분석, 텍스트 전처리, 파일 관리)
  - 웹 기반 사용자 인터페이스
  - 크로스플랫폼 실행 스크립트 (run.sh, run.bat, run.py)
  - 의존성 업데이트 (pydantic v2, numpy v2 지원)
  - 조건부 AI 모듈 로딩 (transformers 선택적)
  - librosa 최신 버전 호환성 개선

### v0.8.0
- 최적화 및 문서화 완료
  - setup.py 및 pyproject.toml (표준 Python 패키징)
  - 콘솔 스크립트 엔트리포인트 (pvtts-* 명령어)
  - PyPI 배포 준비 완료
  - LICENSE 파일 (MIT)
  - .gitignore 및 MANIFEST.in
  - 코드 품질 도구 설정 (black, flake8, mypy)
  - pytest 설정 및 커버리지
  - 상세한 설치 가이드 (docs/installation.md)
  - 빠른 시작 가이드 (docs/quickstart.md)
  - 예제 코드 (examples/)
    - basic_synthesis.py: 기본 합성
    - tts_collage.py: TTS-to-Collage
    - batch_processing.py: 배치 처리
  - 선택적 의존성 (ai, tts, gui, dev, all)
  - 프로덕션 준비 완료

### v0.7.0
- GUI 구현
  - PyQt6 기반 메인 애플리케이션
  - 오디오 플레이어 위젯 (재생, 일시정지, 정지, 볼륨, 시크)
  - 파형 및 스펙트로그램 시각화 위젯 (Matplotlib 기반)
  - 오디오 합성 패널 (타겟/소스 선택, 알고리즘 선택, 실시간 시각화)
  - TTS 패널 (텍스트 입력, 백엔드 선택, 콜라주 옵션)
  - 배치 처리 패널 (워크플로 선택, 진행 상황 추적, 로그 뷰어)
  - 설정 대화상자 (일반, 오디오, 알고리즘 설정)
  - 도움말 대화상자 (사용 가이드)
  - QThread 기반 비동기 처리 (UI 프리징 방지)
  - 실시간 진행률 표시 및 취소 기능
  - GUI 설정 파일 (config/gui.yml)

### v0.6.0
- 배치 처리 및 워크플로 자동화 구현
  - BatchProcessor (다중 작업 병렬 처리)
  - JobQueue (작업 큐 및 의존성 관리)
  - ProgressTracker (실시간 진행률 추적)
  - ErrorHandler (오류 처리 및 재시도)
  - ResultAggregator (결과 집계 및 요약)
  - Pipeline (파이프라인 스테이지 구성)
  - 워크플로 템플릿 (TTS Collage, Audio Matching, Batch Synthesis)
  - 배치 처리 CLI (run, list-workflows, benchmark 명령어)
  - 병렬 처리 지원 (프로세스/스레드 선택)
  - 포괄적인 테스트 스위트

### v0.5.0
- TTS 통합 구현
  - 3가지 TTS 백엔드 (gTTS, pyttsx3, Edge-TTS)
  - 텍스트 전처리 (숫자/약어 변환, 문장 분리)
  - TTS-to-Collage 파이프라인 (텍스트 → TTS → 콜라주)
  - 배치 TTS 처리
  - TTS CLI (speak, collage, batch 명령어)
  - 폴백 전략 및 오류 처리

### v0.4.0
- 오디오 합성 엔진 구현
  - 세그먼트 추출 및 검증
  - 4가지 블렌딩 알고리즘 (linear, logarithmic, equal_power, spectral)
  - 피치 및 템포 조정
  - 프로소디 매칭 (피치, 에너지, 길이)
  - 품질 향상 (노이즈 감소, 스펙트럼 스무딩)
  - 콜라주 엔진 (전체 파이프라인)
  - 품질 메트릭 (SNR, MSE, 스펙트럼 거리)
  - LRU 세그먼트 캐시
  - 합성 CLI 및 시각화

### v0.3.0
- AI 기반 유사도 검출 구현
  - Wav2Vec2, HuBERT 모델 지원
  - 임베딩 기반 유사도 매칭
  - 하이브리드 알고리즘 (전통적 + AI)
  - AI 메타데이터 및 주파수 분석
  - AI CLI 도구

### v0.2.0
- 전통적인 유사도 검출 알고리즘 구현
  - MFCC, 스펙트럼, 에너지, 리듬 기반 매칭
  - 앙상블 알고리즘 지원
  - 세그먼트 매처 및 알고리즘 매니저
  - 유사도 검출 CLI 도구
  - 포괄적인 테스트 스위트

### v0.1.0
- 프로젝트 초기 설정
- 기본 오디오 I/O 및 분석 모듈
- 설정 시스템
- 기본 CLI 도구