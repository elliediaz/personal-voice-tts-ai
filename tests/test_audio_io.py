"""
Tests for Audio I/O Module
"""

import pytest
import numpy as np
from pathlib import Path

from core.audio.io import AudioFile


class TestAudioFile:
    """AudioFile 클래스 테스트"""

    def test_init_mono(self, sample_audio_mono):
        """모노 오디오 초기화 테스트"""
        audio_data, sample_rate = sample_audio_mono
        audio = AudioFile(audio_data, sample_rate)

        assert audio.sample_rate == sample_rate
        assert audio.channels == 1
        assert len(audio.data) == len(audio_data)
        assert audio.duration == pytest.approx(1.0, rel=0.01)

    def test_init_stereo(self, sample_audio_stereo):
        """스테레오 오디오 초기화 테스트"""
        audio_data, sample_rate = sample_audio_stereo
        audio = AudioFile(audio_data, sample_rate)

        assert audio.sample_rate == sample_rate
        assert audio.channels == 2
        assert audio.duration == pytest.approx(1.0, rel=0.01)

    def test_load_file(self, temp_audio_file):
        """파일 로딩 테스트"""
        audio = AudioFile.load(temp_audio_file)

        assert audio.sample_rate > 0
        assert audio.channels > 0
        assert audio.duration > 0
        assert audio.file_path == temp_audio_file

    def test_load_nonexistent_file(self):
        """존재하지 않는 파일 로딩 시 예외 발생 테스트"""
        with pytest.raises(FileNotFoundError):
            AudioFile.load("nonexistent_file.wav")

    def test_save_wav(self, tmp_path, sample_audio_mono):
        """WAV 저장 테스트"""
        audio_data, sample_rate = sample_audio_mono
        audio = AudioFile(audio_data, sample_rate)

        output_path = tmp_path / "output.wav"
        saved_path = audio.save(output_path)

        assert saved_path.exists()
        assert saved_path.suffix == ".wav"

        # 저장된 파일 로드하여 검증
        loaded_audio = AudioFile.load(saved_path)
        assert loaded_audio.sample_rate == sample_rate
        assert np.allclose(loaded_audio.data, audio_data, atol=1e-5)

    def test_to_mono(self, sample_audio_stereo):
        """스테레오를 모노로 변환 테스트"""
        audio_data, sample_rate = sample_audio_stereo
        audio = AudioFile(audio_data, sample_rate)

        mono_audio = audio.to_mono()

        assert mono_audio.channels == 1
        assert len(mono_audio.data.shape) == 1 or mono_audio.data.shape[1] == 1

    def test_resample(self, sample_audio_mono):
        """리샘플링 테스트"""
        audio_data, sample_rate = sample_audio_mono
        audio = AudioFile(audio_data, sample_rate)

        target_sr = 16000
        resampled_audio = audio.resample(target_sr)

        assert resampled_audio.sample_rate == target_sr
        assert len(resampled_audio.data) != len(audio_data)

    def test_normalize(self, sample_audio_mono):
        """정규화 테스트"""
        audio_data, sample_rate = sample_audio_mono
        # 진폭을 0.5로 스케일링
        audio_data = audio_data * 0.5
        audio = AudioFile(audio_data, sample_rate)

        normalized_audio = audio.normalize()

        assert np.max(np.abs(normalized_audio.data)) == pytest.approx(1.0, rel=0.01)

    def test_duration_property(self, sample_audio_mono):
        """길이 속성 테스트"""
        audio_data, sample_rate = sample_audio_mono
        audio = AudioFile(audio_data, sample_rate)

        expected_duration = len(audio_data) / sample_rate
        assert audio.duration == pytest.approx(expected_duration, rel=0.01)

    def test_num_samples_property(self, sample_audio_mono):
        """샘플 수 속성 테스트"""
        audio_data, sample_rate = sample_audio_mono
        audio = AudioFile(audio_data, sample_rate)

        assert audio.num_samples == len(audio_data)

    def test_repr(self, sample_audio_mono):
        """문자열 표현 테스트"""
        audio_data, sample_rate = sample_audio_mono
        audio = AudioFile(audio_data, sample_rate)

        repr_str = repr(audio)
        assert "AudioFile" in repr_str
        assert str(sample_rate) in repr_str
