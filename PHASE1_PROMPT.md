# Phase 1: Foundation & Basic Audio Processing

## Goal
Set up project structure and basic audio I/O capabilities

---

## Prompt for Claude Code

```
Implement the foundation layer for an audio synthesis and collaging system with the following requirements:

1. PROJECT SETUP
   - Create Python project with proper package structure
   - Set up dependency management (requirements.txt or pyproject.toml)
   - Configure pytest for testing
   - Create configuration system using YAML/JSON

2. AUDIO I/O MODULE (core/audio/io.py)
   - Implement AudioFile class for loading/saving audio files
   - Support formats: WAV, MP3, FLAC, OGG
   - Extract metadata: sample rate, channels, duration, bit depth
   - Implement proper error handling
   - Use librosa, soundfile, or pydub for audio operations

3. AUDIO ANALYSIS MODULE (core/audio/analysis.py)
   - Implement basic audio analysis functions:
     * Spectrogram generation
     * Mel-spectrogram
     * Waveform visualization
     * Energy computation
     * Zero-crossing rate
   - All functions should accept numpy arrays
   - Return both numerical data and visualization-ready formats

4. METADATA MODULE (core/audio/metadata.py)
   - Extract and store audio metadata
   - Compute audio fingerprints
   - Generate visualization metadata for GUI later

5. CONFIGURATION SYSTEM (config/)
   - Create default configuration file (config.default.yml)
   - Support for user overrides (config.yml, not in git)
   - Configuration schema validation
   - Settings categories:
     * Audio processing parameters
     * Algorithm selection
     * Output preferences
     * Performance tuning

6. BASIC CLI (cli/basic.py)
   - Command to load and display audio info
   - Command to generate spectrograms
   - Command to test audio I/O
   - Use argparse or click

7. TESTING
   - Unit tests for all modules
   - Test fixtures with sample audio
   - Mock external dependencies

TECHNICAL REQUIREMENTS:
- Python 3.9+
- Type hints throughout
- Docstrings in Korean
- Clean, modular code
- Professional logging
- No emojis in code or output

DELIVERABLES:
- Working audio I/O system
- Basic analysis capabilities
- CLI for testing
- Comprehensive test suite
- Configuration system

Code comments and docstrings should be in Korean, but maintain English for variable/function names.
```

---

## Expected Project Structure After Phase 1

```
personal-voice-tts-ai/
├── core/
│   ├── __init__.py
│   └── audio/
│       ├── __init__.py
│       ├── io.py           # Audio I/O operations
│       ├── analysis.py     # Audio analysis functions
│       └── metadata.py     # Metadata extraction
├── cli/
│   ├── __init__.py
│   └── basic.py           # Basic CLI commands
├── config/
│   ├── config.default.yml # Default configuration
│   └── __init__.py
├── utils/
│   ├── __init__.py
│   ├── logging.py         # Logging utilities
│   └── validators.py      # Input validation
├── tests/
│   ├── __init__.py
│   ├── conftest.py        # pytest configuration
│   ├── test_audio_io.py
│   ├── test_analysis.py
│   └── fixtures/          # Test audio files
├── requirements.txt       # Base dependencies
├── requirements-dev.txt   # Development dependencies
├── setup.py              # Package setup
├── pytest.ini            # pytest configuration
└── .gitignore

```

---

## Key Dependencies for Phase 1

```txt
# Core audio processing
numpy>=1.21.0
scipy>=1.7.0
librosa>=0.9.0
soundfile>=0.11.0
pydub>=0.25.1

# Configuration
PyYAML>=6.0
pydantic>=1.9.0

# CLI
click>=8.0.0

# Visualization (for spectrogram generation)
matplotlib>=3.5.0

# Utilities
python-dotenv>=0.19.0
```

---

## Testing Checklist

After completing Phase 1, verify:

- [ ] Can load WAV, MP3, FLAC, OGG files
- [ ] Can save audio files in different formats
- [ ] Can extract audio metadata (sample rate, channels, duration)
- [ ] Can generate spectrograms
- [ ] Can generate mel-spectrograms
- [ ] Can compute energy and zero-crossing rate
- [ ] CLI commands work correctly
- [ ] Configuration loading works
- [ ] All unit tests pass
- [ ] Code follows style guidelines (type hints, Korean docstrings)
- [ ] No emojis in code or output
- [ ] Proper error handling for invalid files
- [ ] Logging is working properly

---

## Git Commit Message Template

```
기능: 프로젝트 기초 구조 및 오디오 I/O 모듈 구현

- 프로젝트 디렉토리 구조 생성
- 오디오 파일 로딩 및 저장 기능 구현 (WAV, MP3, FLAC, OGG)
- 기본 오디오 분석 함수 구현 (스펙트로그램, 에너지 등)
- 메타데이터 추출 모듈 구현
- 설정 시스템 구축
- 기본 CLI 인터페이스 구현
- 테스트 스위트 작성
```

---

## Notes for Developer

1. Start by creating the directory structure
2. Implement core/audio/io.py first - this is the foundation
3. Add unit tests as you implement each module
4. Use type hints consistently
5. Write docstrings in Korean for all public functions
6. Test with various audio file formats
7. Ensure proper error handling for corrupted/invalid files
8. Consider memory efficiency for large audio files
9. Use logging instead of print statements
10. Commit frequently with clear messages

---

## Next Steps After Phase 1

Once Phase 1 is complete and all tests pass:
1. Review code quality and refactor if needed
2. Update README.md with installation and usage instructions
3. Commit all changes
4. Move to Phase 2: Traditional Similarity Detection

Refer to CLAUDE.md for the complete Phase 2 prompt.
