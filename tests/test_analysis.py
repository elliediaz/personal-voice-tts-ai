"""
Tests for Audio Analysis Module
"""

import pytest
import numpy as np

from core.audio.analysis import AudioAnalyzer


class TestAudioAnalyzer:
    """AudioAnalyzer 클래스 테스트"""

    def test_init_default(self):
        """기본 초기화 테스트"""
        analyzer = AudioAnalyzer()

        assert analyzer.n_fft > 0
        assert analyzer.hop_length > 0
        assert analyzer.n_mels > 0
        assert analyzer.n_mfcc > 0

    def test_compute_spectrogram(self, analyzer, sample_audio_mono):
        """스펙트로그램 계산 테스트"""
        audio_data, sample_rate = sample_audio_mono
        spectrogram = analyzer.compute_spectrogram(audio_data, sample_rate)

        assert spectrogram.ndim == 2
        assert spectrogram.shape[0] > 0
        assert spectrogram.shape[1] > 0

    def test_compute_mel_spectrogram(self, analyzer, sample_audio_mono):
        """멜-스펙트로그램 계산 테스트"""
        audio_data, sample_rate = sample_audio_mono
        mel_spec = analyzer.compute_mel_spectrogram(audio_data, sample_rate)

        assert mel_spec.ndim == 2
        assert mel_spec.shape[0] == analyzer.n_mels
        assert mel_spec.shape[1] > 0

    def test_compute_mfcc(self, analyzer, sample_audio_mono):
        """MFCC 계산 테스트"""
        audio_data, sample_rate = sample_audio_mono
        mfcc = analyzer.compute_mfcc(audio_data, sample_rate)

        assert mfcc.ndim == 2
        assert mfcc.shape[0] == analyzer.n_mfcc
        assert mfcc.shape[1] > 0

    def test_compute_energy(self, analyzer, sample_audio_mono):
        """에너지 계산 테스트"""
        audio_data, sample_rate = sample_audio_mono
        energy = analyzer.compute_energy(audio_data)

        assert energy.ndim == 1
        assert len(energy) > 0
        assert np.all(energy >= 0)

    def test_compute_zero_crossing_rate(self, analyzer, sample_audio_mono):
        """제로크로싱율 계산 테스트"""
        audio_data, sample_rate = sample_audio_mono
        zcr = analyzer.compute_zero_crossing_rate(audio_data)

        assert zcr.ndim == 1
        assert len(zcr) > 0
        assert np.all(zcr >= 0)
        assert np.all(zcr <= 1)

    def test_compute_spectral_centroid(self, analyzer, sample_audio_mono):
        """스펙트럼 중심 계산 테스트"""
        audio_data, sample_rate = sample_audio_mono
        centroid = analyzer.compute_spectral_centroid(audio_data, sample_rate)

        assert centroid.ndim == 1
        assert len(centroid) > 0
        assert np.all(centroid >= 0)

    def test_compute_spectral_rolloff(self, analyzer, sample_audio_mono):
        """스펙트럼 롤오프 계산 테스트"""
        audio_data, sample_rate = sample_audio_mono
        rolloff = analyzer.compute_spectral_rolloff(audio_data, sample_rate)

        assert rolloff.ndim == 1
        assert len(rolloff) > 0
        assert np.all(rolloff >= 0)

    def test_visualize_waveform(self, analyzer, sample_audio_mono):
        """파형 시각화 테스트"""
        audio_data, sample_rate = sample_audio_mono
        fig = analyzer.visualize_waveform(audio_data, sample_rate)

        assert fig is not None
        plt.close(fig)

    def test_visualize_spectrogram(self, analyzer, sample_audio_mono):
        """스펙트로그램 시각화 테스트"""
        audio_data, sample_rate = sample_audio_mono
        spectrogram = analyzer.compute_spectrogram(audio_data, sample_rate)
        fig = analyzer.visualize_spectrogram(spectrogram, sample_rate)

        assert fig is not None
        plt.close(fig)

    def test_visualize_mel_spectrogram(self, analyzer, sample_audio_mono):
        """멜-스펙트로그램 시각화 테스트"""
        audio_data, sample_rate = sample_audio_mono
        mel_spec = analyzer.compute_mel_spectrogram(audio_data, sample_rate)
        fig = analyzer.visualize_mel_spectrogram(mel_spec, sample_rate)

        assert fig is not None
        plt.close(fig)


# matplotlib import for cleanup
import matplotlib.pyplot as plt
