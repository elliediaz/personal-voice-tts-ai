"""
Tests for Synthesis Modules
"""

import pytest
import numpy as np

from core.synthesis.extractor import SegmentExtractor
from core.synthesis.blending import AudioBlender
from core.synthesis.pitch import PitchAdjuster
from core.synthesis.tempo import TempoAdjuster
from core.synthesis.prosody import ProsodyMatcher
from core.synthesis.enhancement import QualityEnhancer
from core.synthesis.metrics import QualityMetrics
from core.synthesis.cache import SegmentCache
from algorithms.base import SimilarityMatch


class TestSegmentExtractor:
    """SegmentExtractor 테스트"""

    def test_init(self):
        """초기화 테스트"""
        extractor = SegmentExtractor(fade_duration=0.01, min_segment_length=0.1)

        assert extractor.fade_duration == 0.01
        assert extractor.min_segment_length == 0.1

    def test_extract(self, sample_audio_mono):
        """세그먼트 추출 테스트"""
        audio_data, sample_rate = sample_audio_mono

        extractor = SegmentExtractor()
        segment, sr = extractor.extract(audio_data, sample_rate, 0.5, 1.5)

        assert isinstance(segment, np.ndarray)
        assert sr == sample_rate
        assert len(segment) > 0

    def test_extract_from_match(self, sample_audio_mono):
        """매치로부터 추출 테스트"""
        audio_data, sample_rate = sample_audio_mono

        match = SimilarityMatch(
            target_start=0.0,
            target_end=1.0,
            source_start=0.5,
            source_end=1.5,
            similarity=0.8,
        )

        extractor = SegmentExtractor()
        segment, sr = extractor.extract_from_match(audio_data, sample_rate, match)

        assert isinstance(segment, np.ndarray)
        assert sr == sample_rate

    def test_validate_segment(self, sample_audio_mono):
        """세그먼트 검증 테스트"""
        audio_data, sample_rate = sample_audio_mono

        extractor = SegmentExtractor()
        segment, sr = extractor.extract(audio_data, sample_rate, 0.5, 1.5)

        is_valid = extractor.validate_segment(segment, sr)

        assert isinstance(is_valid, bool)


class TestAudioBlender:
    """AudioBlender 테스트"""

    def test_init(self):
        """초기화 테스트"""
        blender = AudioBlender(blend_algorithm="equal_power", crossfade_duration=0.05)

        assert blender.blend_algorithm == "equal_power"
        assert blender.crossfade_duration == 0.05

    def test_crossfade(self, sample_audio_mono):
        """크로스페이드 테스트"""
        audio_data, sample_rate = sample_audio_mono

        blender = AudioBlender()
        blended = blender.crossfade(audio_data, audio_data, sample_rate)

        assert isinstance(blended, np.ndarray)
        assert len(blended) > 0

    def test_blend_segments(self, sample_audio_mono):
        """세그먼트 블렌딩 테스트"""
        audio_data, sample_rate = sample_audio_mono

        segments = [audio_data[:8000], audio_data[8000:16000]]

        blender = AudioBlender()
        blended = blender.blend_segments(segments, sample_rate)

        assert isinstance(blended, np.ndarray)


class TestPitchAdjuster:
    """PitchAdjuster 테스트"""

    def test_init(self):
        """초기화 테스트"""
        adjuster = PitchAdjuster(method="phase_vocoder")

        assert adjuster.method == "phase_vocoder"

    def test_adjust_pitch(self, sample_audio_mono):
        """피치 조정 테스트"""
        audio_data, sample_rate = sample_audio_mono

        adjuster = PitchAdjuster()
        adjusted = adjuster.adjust_pitch(audio_data, sample_rate, n_steps=2)

        assert isinstance(adjusted, np.ndarray)
        assert len(adjusted) > 0


class TestTempoAdjuster:
    """TempoAdjuster 테스트"""

    def test_init(self):
        """초기화 테스트"""
        adjuster = TempoAdjuster(preserve_pitch=True)

        assert adjuster.preserve_pitch == True

    def test_adjust_tempo(self, sample_audio_mono):
        """템포 조정 테스트"""
        audio_data, sample_rate = sample_audio_mono

        adjuster = TempoAdjuster()
        adjusted = adjuster.adjust_tempo(audio_data, sample_rate, rate=1.5)

        assert isinstance(adjusted, np.ndarray)
        assert len(adjusted) > 0


class TestProsodyMatcher:
    """ProsodyMatcher 테스트"""

    def test_init(self):
        """초기화 테스트"""
        matcher = ProsodyMatcher(match_pitch=True, match_energy=True)

        assert matcher.match_pitch == True
        assert matcher.match_energy == True

    def test_extract_prosody_features(self, sample_audio_mono):
        """프로소디 특징 추출 테스트"""
        audio_data, sample_rate = sample_audio_mono

        matcher = ProsodyMatcher()
        features = matcher.extract_prosody_features(audio_data, sample_rate)

        assert isinstance(features, dict)
        assert "pitch_mean" in features
        assert "energy_mean" in features


class TestQualityEnhancer:
    """QualityEnhancer 테스트"""

    def test_init(self):
        """초기화 테스트"""
        enhancer = QualityEnhancer(noise_reduction=True)

        assert enhancer.noise_reduction == True

    def test_enhance(self, sample_audio_mono):
        """품질 향상 테스트"""
        audio_data, sample_rate = sample_audio_mono

        enhancer = QualityEnhancer()
        enhanced = enhancer.enhance(audio_data, sample_rate)

        assert isinstance(enhanced, np.ndarray)
        assert len(enhanced) == len(audio_data)


class TestQualityMetrics:
    """QualityMetrics 테스트"""

    def test_compute_snr(self, sample_audio_mono):
        """SNR 계산 테스트"""
        audio_data, sample_rate = sample_audio_mono

        metrics = QualityMetrics()
        snr = metrics.compute_snr(audio_data, audio_data)

        assert isinstance(snr, float)

    def test_analyze_quality(self, sample_audio_mono):
        """품질 분석 테스트"""
        audio_data, sample_rate = sample_audio_mono

        metrics = QualityMetrics()
        results = metrics.analyze_quality(audio_data, sample_rate)

        assert isinstance(results, dict)
        assert "rms_energy" in results
        assert "clipping" in results
        assert "silence" in results

    def test_get_quality_score(self, sample_audio_mono):
        """품질 점수 테스트"""
        audio_data, sample_rate = sample_audio_mono

        metrics = QualityMetrics()
        results = metrics.analyze_quality(audio_data, sample_rate)
        score = metrics.get_quality_score(results)

        assert 0.0 <= score <= 1.0


class TestSegmentCache:
    """SegmentCache 테스트"""

    def test_init(self):
        """초기화 테스트"""
        cache = SegmentCache(max_size=10)

        assert cache.max_size == 10
        assert len(cache) == 0

    def test_put_get(self, sample_audio_mono):
        """저장 및 가져오기 테스트"""
        audio_data, sample_rate = sample_audio_mono

        cache = SegmentCache()

        # 저장
        cache.put("test.wav", 0.0, 1.0, audio_data, sample_rate)

        # 가져오기
        result = cache.get("test.wav", 0.0, 1.0)

        assert result is not None
        segment, sr = result
        assert isinstance(segment, np.ndarray)
        assert sr == sample_rate

    def test_cache_miss(self):
        """캐시 미스 테스트"""
        cache = SegmentCache()

        result = cache.get("nonexistent.wav", 0.0, 1.0)

        assert result is None

    def test_get_stats(self):
        """통계 테스트"""
        cache = SegmentCache()
        stats = cache.get_stats()

        assert isinstance(stats, dict)
        assert "size" in stats
        assert "hit_rate" in stats
