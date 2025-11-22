# 빠른 시작 가이드

이 가이드는 Personal Voice TTS AI의 기본 사용법을 설명합니다.

## 1. 기본 오디오 분석

### CLI 사용

```bash
# 오디오 파일 정보 확인
pvtts-basic info audio.wav

# 스펙트로그램 생성
pvtts-basic spectrogram audio.wav --output spectrogram.png
```

### Python API 사용

```python
from core.audio.io import AudioFile
from core.audio.analysis import AudioAnalyzer

# 오디오 로드
audio_file = AudioFile("audio.wav")
audio_data, sample_rate = audio_file.load()

# 분석
analyzer = AudioAnalyzer()
spectrogram = analyzer.compute_spectrogram(audio_data, sample_rate)
```

## 2. 유사도 검출

### 전통적인 방법 (MFCC)

```bash
# CLI
pvtts-similarity find \
  --target target.wav \
  --source source.wav \
  --algorithm mfcc \
  --threshold 0.5
```

```python
# Python API
from algorithms.traditional.mfcc import MFCCSimilarity
import soundfile as sf

# 오디오 로드
target, sr1 = sf.read("target.wav")
source, sr2 = sf.read("source.wav")

# 유사도 계산
mfcc_algo = MFCCSimilarity()
similarity = mfcc_algo.compare(target, sr1, source, sr2)
print(f"유사도: {similarity}")
```

### AI 기반 방법

```bash
# CLI
pvtts-ai find \
  --target target.wav \
  --source source.wav \
  --model wav2vec2-base
```

```python
# Python API
from algorithms.ai_based.embedding_matcher import EmbeddingMatcher
import soundfile as sf

# 오디오 로드
target, sr = sf.read("target.wav")
source, _ = sf.read("source.wav")

# AI 유사도 계산
matcher = EmbeddingMatcher(model_name="wav2vec2-base")
similarity = matcher.compare(target, source, sr)
```

## 3. 오디오 합성

### 기본 합성

```bash
# CLI
pvtts-synthesize \
  --target target.wav \
  --sources source1.wav source2.wav source3.wav \
  --output output.wav \
  --algorithm hybrid
```

```python
# Python API
from core.synthesis.engine import CollageEngine
from algorithms.ai_based.hybrid import HybridSimilarity
from pathlib import Path

# 합성 엔진 생성
sim_algo = HybridSimilarity()
engine = CollageEngine(similarity_algorithm=sim_algo)

# 합성 실행
metadata = engine.synthesize_from_file(
    target_file=Path("target.wav"),
    source_files=[Path("source1.wav"), Path("source2.wav")],
    output_path=Path("output.wav")
)

print(f"합성 완료: {metadata}")
```

## 4. TTS (Text-to-Speech)

### 기본 TTS

```bash
# CLI
pvtts-tts speak \
  --text "안녕하세요. 테스트입니다." \
  --output speech.wav \
  --backend gtts
```

```python
# Python API
from core.tts.backends import GTTSBackend

# TTS 엔진 생성
tts = GTTSBackend(language="ko")

# 음성 생성
audio_data, sample_rate = tts.synthesize(
    text="안녕하세요. 테스트입니다.",
    output_path="speech.wav"
)
```

### TTS-to-Collage

```bash
# CLI
pvtts-tts collage \
  --text "안녕하세요" \
  --sources voice1.wav voice2.wav \
  --output collage.wav \
  --backend gtts
```

```python
# Python API
from core.tts.pipeline import TTSPipeline
from core.tts.backends import GTTSBackend
from algorithms.traditional.mfcc import MFCCSimilarity
from pathlib import Path

# 파이프라인 생성
tts_backend = GTTSBackend(language="ko")
sim_algo = MFCCSimilarity()
pipeline = TTSPipeline(tts_engine=tts_backend, similarity_algorithm=sim_algo)

# 콜라주 생성
metadata = pipeline.synthesize_collage(
    text="안녕하세요",
    source_files=[Path("voice1.wav"), Path("voice2.wav")],
    output_path=Path("collage.wav")
)
```

## 5. 배치 처리

### 텍스트 파일 준비

`inputs.txt`:
```
안녕하세요
반갑습니다
좋은 하루 되세요
```

### 배치 실행

```bash
# CLI
pvtts-batch run tts_collage \
  inputs.txt \
  source1.wav source2.wav source3.wav \
  --output-dir outputs/ \
  --max-workers 4
```

```python
# Python API
from core.batch.processor import BatchProcessor
from core.tts.pipeline import TTSPipeline
from pathlib import Path

# 배치 프로세서 생성
processor = BatchProcessor(max_workers=4)

# 입력 파일 읽기
with open("inputs.txt") as f:
    texts = [line.strip() for line in f]

# 작업 추가
for i, text in enumerate(texts):
    processor.add_job(
        job_id=f"job_{i}",
        func=pipeline.synthesize_collage,
        kwargs={
            "text": text,
            "source_files": [Path("source1.wav")],
            "output_path": Path(f"outputs/output_{i}.wav")
        }
    )

# 실행
summary = processor.process_all()
print(summary)
```

## 6. GUI 사용

GUI를 실행하려면:

```bash
pvtts-gui
```

또는:

```bash
python -m gui.app
```

## 다음 단계

- [상세 사용법](usage.md)
- [API 문서](api.md)
- [설정 가이드](configuration.md)
- [예제 모음](../examples/)
