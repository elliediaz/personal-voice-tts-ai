# 설치 가이드

## 시스템 요구사항

### 최소 요구사항
- Python 3.9 이상
- 4GB RAM
- 2GB 디스크 공간

### 권장 요구사항
- Python 3.10 이상
- 8GB RAM (AI 모델 사용 시)
- CUDA 지원 GPU (선택사항)
- 10GB 디스크 공간

## 설치 방법

### 1. 기본 설치

가장 간단한 방법은 pip를 사용하는 것입니다:

```bash
pip install personal-voice-tts-ai
```

### 2. 소스에서 설치

개발 버전을 사용하려면:

```bash
# 저장소 클론
git clone https://github.com/yourusername/personal-voice-tts-ai.git
cd personal-voice-tts-ai

# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 기본 패키지 설치
pip install -e .
```

### 3. 선택적 기능 설치

#### AI 기반 분석
```bash
pip install personal-voice-tts-ai[ai]
```

#### TTS 기능
```bash
pip install personal-voice-tts-ai[tts]
```

#### GUI
```bash
pip install personal-voice-tts-ai[gui]
```

#### 개발 도구
```bash
pip install personal-voice-tts-ai[dev]
```

#### 모든 기능
```bash
pip install personal-voice-tts-ai[all]
```

## 설치 확인

설치가 제대로 되었는지 확인:

```bash
# CLI 명령어 확인
pvtts-basic --help
pvtts-similarity --help
pvtts-tts --help

# Python에서 확인
python -c "import core; print('설치 성공!')"
```

## GPU 지원 (선택사항)

AI 기반 분석을 GPU에서 실행하려면:

```bash
# CUDA 11.8용 PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# CUDA 12.1용 PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

## 문제 해결

### ImportError: No module named 'librosa'

librosa 설치 실패 시:

```bash
# 시스템 의존성 설치 (Ubuntu/Debian)
sudo apt-get install libsndfile1

# 시스템 의존성 설치 (macOS)
brew install libsndfile

# librosa 재설치
pip install --upgrade librosa
```

### PyQt6 설치 오류

GUI를 사용하지 않는다면 건너뛰어도 됩니다:

```bash
# GUI 없이 설치
pip install personal-voice-tts-ai
```

### CUDA 관련 오류

GPU가 없거나 CUDA를 사용하지 않는다면:

```bash
# CPU 버전으로 설치
pip install personal-voice-tts-ai[ai]  # 기본적으로 CPU 버전
```

## 다음 단계

설치가 완료되면:
- [빠른 시작 가이드](quickstart.md)를 참조하세요
- [사용 예제](../examples/)를 확인하세요
- [API 문서](api.md)를 읽어보세요
