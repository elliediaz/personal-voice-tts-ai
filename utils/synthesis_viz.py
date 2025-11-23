"""
Synthesis Visualization

오디오 합성 시각화 유틸리티
"""

import logging
from pathlib import Path
from typing import Optional

import numpy as np
import matplotlib.pyplot as plt
import librosa
import librosa.display

logger = logging.getLogger(__name__)


class SynthesisVisualizer:
    """합성 시각화 클래스"""

    def __init__(self, figsize: tuple = (12, 8)):
        """
        Args:
            figsize: 그림 크기
        """
        self.figsize = figsize

        logger.info("SynthesisVisualizer 초기화")

    def compare_waveforms(
        self,
        audio1: np.ndarray,
        audio2: np.ndarray,
        sr: int,
        labels: tuple = ("Target", "Synthesized"),
        output_path: Optional[Path] = None,
    ):
        """
        파형 비교 시각화

        Args:
            audio1: 첫 번째 오디오
            audio2: 두 번째 오디오
            sr: 샘플링 레이트
            labels: 레이블 튜플
            output_path: 저장 경로 (옵션)
        """
        fig, axes = plt.subplots(2, 1, figsize=self.figsize)

        # 첫 번째 파형
        librosa.display.waveshow(audio1, sr=sr, ax=axes[0])
        axes[0].set_title(labels[0])
        axes[0].set_xlabel("Time (s)")
        axes[0].set_ylabel("Amplitude")

        # 두 번째 파형
        librosa.display.waveshow(audio2, sr=sr, ax=axes[1])
        axes[1].set_title(labels[1])
        axes[1].set_xlabel("Time (s)")
        axes[1].set_ylabel("Amplitude")

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches="tight")
            logger.info(f"파형 비교 저장: {output_path}")
        else:
            plt.show()

        plt.close(fig)

    def compare_spectrograms(
        self,
        audio1: np.ndarray,
        audio2: np.ndarray,
        sr: int,
        labels: tuple = ("Target", "Synthesized"),
        output_path: Optional[Path] = None,
    ):
        """
        스펙트로그램 비교 시각화

        Args:
            audio1: 첫 번째 오디오
            audio2: 두 번째 오디오
            sr: 샘플링 레이트
            labels: 레이블 튜플
            output_path: 저장 경로 (옵션)
        """
        fig, axes = plt.subplots(2, 1, figsize=self.figsize)

        # 첫 번째 스펙트로그램
        D1 = librosa.amplitude_to_db(
            np.abs(librosa.stft(audio1)), ref=np.max
        )
        img1 = librosa.display.specshow(
            D1, sr=sr, x_axis="time", y_axis="hz", ax=axes[0]
        )
        axes[0].set_title(f"{labels[0]} Spectrogram")
        fig.colorbar(img1, ax=axes[0], format="%+2.0f dB")

        # 두 번째 스펙트로그램
        D2 = librosa.amplitude_to_db(
            np.abs(librosa.stft(audio2)), ref=np.max
        )
        img2 = librosa.display.specshow(
            D2, sr=sr, x_axis="time", y_axis="hz", ax=axes[1]
        )
        axes[1].set_title(f"{labels[1]} Spectrogram")
        fig.colorbar(img2, ax=axes[1], format="%+2.0f dB")

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches="tight")
            logger.info(f"스펙트로그램 비교 저장: {output_path}")
        else:
            plt.show()

        plt.close(fig)

    def visualize_synthesis_timeline(
        self,
        segments: list,
        total_duration: float,
        output_path: Optional[Path] = None,
    ):
        """
        합성 타임라인 시각화

        Args:
            segments: 세그먼트 리스트 (start, end, label)
            total_duration: 전체 길이 (초)
            output_path: 저장 경로 (옵션)
        """
        fig, ax = plt.subplots(figsize=self.figsize)

        # 세그먼트 그리기
        for i, (start, end, label) in enumerate(segments):
            duration = end - start
            ax.barh(0, duration, left=start, height=0.5, label=label if i == 0 else "")

        ax.set_xlim(0, total_duration)
        ax.set_ylim(-0.5, 0.5)
        ax.set_xlabel("Time (s)")
        ax.set_title("Synthesis Timeline")
        ax.set_yticks([])

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches="tight")
            logger.info(f"타임라인 저장: {output_path}")
        else:
            plt.show()

        plt.close(fig)

    def plot_quality_metrics(
        self,
        metrics: dict,
        output_path: Optional[Path] = None,
    ):
        """
        품질 메트릭 시각화

        Args:
            metrics: 메트릭 딕셔너리
            output_path: 저장 경로 (옵션)
        """
        fig, axes = plt.subplots(2, 2, figsize=self.figsize)

        # RMS 에너지
        axes[0, 0].bar(["RMS Energy"], [metrics["rms_energy"]])
        axes[0, 0].set_title("RMS Energy")
        axes[0, 0].set_ylabel("Energy")

        # Zero Crossing Rate
        axes[0, 1].bar(["ZCR"], [metrics["zero_crossing_rate"]])
        axes[0, 1].set_title("Zero Crossing Rate")
        axes[0, 1].set_ylabel("Rate")

        # 스펙트럼 중심
        axes[1, 0].bar(["Spectral Centroid"], [metrics["spectral_centroid"]])
        axes[1, 0].set_title("Spectral Centroid")
        axes[1, 0].set_ylabel("Frequency (Hz)")

        # 클리핑 및 무음
        clipping_ratio = metrics["clipping"]["clipping_ratio"] * 100
        silence_ratio = metrics["silence"]["silence_ratio"] * 100

        axes[1, 1].bar(["Clipping", "Silence"], [clipping_ratio, silence_ratio])
        axes[1, 1].set_title("Clipping & Silence")
        axes[1, 1].set_ylabel("Percentage (%)")

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches="tight")
            logger.info(f"품질 메트릭 저장: {output_path}")
        else:
            plt.show()

        plt.close(fig)

    def __repr__(self) -> str:
        return f"SynthesisVisualizer(figsize={self.figsize})"
