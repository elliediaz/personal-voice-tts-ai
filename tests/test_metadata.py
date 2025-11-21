"""
Tests for Audio Metadata Module
"""

import pytest
import json
from pathlib import Path

from core.audio.metadata import AudioMetadata


class TestAudioMetadata:
    """AudioMetadata 클래스 테스트"""

    def test_from_audio_file(self, temp_audio_file, sample_audio_mono):
        """오디오 파일로부터 메타데이터 생성 테스트"""
        audio_data, sample_rate = sample_audio_mono
        metadata = AudioMetadata.from_audio_file(
            temp_audio_file,
            audio_data,
            sample_rate,
            compute_fingerprint=True,
            compute_statistics=True,
        )

        assert metadata.file_name == "test_audio.wav"
        assert Path(metadata.file_path) == temp_audio_file
        assert metadata.sample_rate == sample_rate
        assert metadata.channels == 1
        assert metadata.duration > 0
        assert metadata.fingerprint is not None
        assert metadata.statistics is not None

    def test_to_dict(self, temp_audio_file, sample_audio_mono):
        """딕셔너리 변환 테스트"""
        audio_data, sample_rate = sample_audio_mono
        metadata = AudioMetadata.from_audio_file(
            temp_audio_file,
            audio_data,
            sample_rate,
        )

        metadata_dict = metadata.to_dict()

        assert isinstance(metadata_dict, dict)
        assert 'file_name' in metadata_dict
        assert 'sample_rate' in metadata_dict
        assert 'duration' in metadata_dict

    def test_to_json(self, temp_audio_file, sample_audio_mono):
        """JSON 변환 테스트"""
        audio_data, sample_rate = sample_audio_mono
        metadata = AudioMetadata.from_audio_file(
            temp_audio_file,
            audio_data,
            sample_rate,
        )

        json_str = metadata.to_json()

        assert isinstance(json_str, str)
        # JSON 파싱 테스트
        json_data = json.loads(json_str)
        assert isinstance(json_data, dict)

    def test_save_and_load(self, tmp_path, temp_audio_file, sample_audio_mono):
        """저장 및 로드 테스트"""
        audio_data, sample_rate = sample_audio_mono
        metadata = AudioMetadata.from_audio_file(
            temp_audio_file,
            audio_data,
            sample_rate,
        )

        # 저장
        output_path = tmp_path / "metadata.json"
        metadata.save(output_path)

        assert output_path.exists()

        # 로드
        loaded_metadata = AudioMetadata.load(output_path)

        assert loaded_metadata.file_name == metadata.file_name
        assert loaded_metadata.sample_rate == metadata.sample_rate
        assert loaded_metadata.duration == pytest.approx(metadata.duration, rel=0.01)

    def test_statistics(self, temp_audio_file, sample_audio_mono):
        """통계 정보 테스트"""
        audio_data, sample_rate = sample_audio_mono
        metadata = AudioMetadata.from_audio_file(
            temp_audio_file,
            audio_data,
            sample_rate,
            compute_statistics=True,
        )

        assert metadata.statistics is not None
        assert 'mean' in metadata.statistics
        assert 'std' in metadata.statistics
        assert 'min' in metadata.statistics
        assert 'max' in metadata.statistics
        assert 'rms' in metadata.statistics

    def test_fingerprint(self, temp_audio_file, sample_audio_mono):
        """지문 계산 테스트"""
        audio_data, sample_rate = sample_audio_mono
        metadata = AudioMetadata.from_audio_file(
            temp_audio_file,
            audio_data,
            sample_rate,
            compute_fingerprint=True,
        )

        assert metadata.fingerprint is not None
        assert len(metadata.fingerprint) == 32  # MD5 해시 길이

        # 동일한 데이터로 다시 생성 시 동일한 지문
        metadata2 = AudioMetadata.from_audio_file(
            temp_audio_file,
            audio_data,
            sample_rate,
            compute_fingerprint=True,
        )

        assert metadata.fingerprint == metadata2.fingerprint

    def test_repr(self, temp_audio_file, sample_audio_mono):
        """문자열 표현 테스트"""
        audio_data, sample_rate = sample_audio_mono
        metadata = AudioMetadata.from_audio_file(
            temp_audio_file,
            audio_data,
            sample_rate,
        )

        repr_str = repr(metadata)
        assert "AudioMetadata" in repr_str
        assert metadata.file_name in repr_str
