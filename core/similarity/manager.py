"""
Algorithm Manager Module

모든 유사도 알고리즘을 관리하고 통합하는 모듈입니다.
"""

from typing import Dict, List, Optional, Type, Any
import time
import numpy as np

from algorithms.base import BaseSimilarityAlgorithm, SimilarityMatch
from algorithms.traditional.mfcc import MFCCSimilarity
from algorithms.traditional.spectral import SpectralSimilarity
from algorithms.traditional.energy import EnergySimilarity
from algorithms.traditional.rhythm import RhythmSimilarity
from algorithms.random.random_matcher import RandomMatcher
from core.similarity.matcher import SegmentMatcher
from utils.logging import get_logger

logger = get_logger(__name__)


class AlgorithmManager:
    """
    유사도 알고리즘 매니저.

    모든 유사도 알고리즘을 등록하고 관리하며, 앙상블 방법을 제공합니다.
    """

    def __init__(self):
        """AlgorithmManager를 초기화합니다."""
        self._algorithms: Dict[str, BaseSimilarityAlgorithm] = {}
        self._register_default_algorithms()
        self.segment_matcher = SegmentMatcher()

        logger.info("AlgorithmManager 초기화 완료")

    def _register_default_algorithms(self):
        """기본 알고리즘들을 등록합니다."""
        default_algorithms = {
            'mfcc': MFCCSimilarity(),
            'spectral': SpectralSimilarity(),
            'energy': EnergySimilarity(),
            'rhythm': RhythmSimilarity(),
            'random': RandomMatcher(),
        }

        for name, algorithm in default_algorithms.items():
            self.register(name, algorithm)

    def register(
        self,
        name: str,
        algorithm: BaseSimilarityAlgorithm,
    ) -> None:
        """
        알고리즘을 등록합니다.

        Args:
            name: 알고리즘 이름
            algorithm: 알고리즘 인스턴스
        """
        self._algorithms[name] = algorithm
        logger.debug(f"알고리즘 등록: {name}")

    def get_algorithm(self, name: str) -> Optional[BaseSimilarityAlgorithm]:
        """
        등록된 알고리즘을 가져옵니다.

        Args:
            name: 알고리즘 이름

        Returns:
            BaseSimilarityAlgorithm: 알고리즘 인스턴스
        """
        return self._algorithms.get(name)

    def list_algorithms(self) -> List[str]:
        """
        등록된 모든 알고리즘 이름을 반환합니다.

        Returns:
            List[str]: 알고리즘 이름 리스트
        """
        return list(self._algorithms.keys())

    def find_similar_segments(
        self,
        algorithm_name: str,
        target_audio: np.ndarray,
        source_audio: np.ndarray,
        target_sr: int,
        source_sr: int,
        top_k: int = 10,
        remove_overlaps: bool = True,
    ) -> List[SimilarityMatch]:
        """
        지정된 알고리즘으로 유사 세그먼트를 찾습니다.

        Args:
            algorithm_name: 사용할 알고리즘 이름
            target_audio: 타겟 오디오
            source_audio: 소스 오디오
            target_sr: 타겟 샘플링 레이트
            source_sr: 소스 샘플링 레이트
            top_k: 반환할 최대 매치 수
            remove_overlaps: 오버랩 제거 여부

        Returns:
            List[SimilarityMatch]: 매칭 결과
        """
        algorithm = self.get_algorithm(algorithm_name)
        if algorithm is None:
            raise ValueError(f"알고리즘을 찾을 수 없습니다: {algorithm_name}")

        logger.info(f"{algorithm_name} 알고리즘으로 유사 세그먼트 검색 시작...")

        start_time = time.time()

        matches = algorithm.find_similar_segments(
            target_audio,
            source_audio,
            target_sr,
            source_sr,
            top_k=top_k * 2 if remove_overlaps else top_k,  # 오버랩 제거 시 여유분 확보
        )

        # 오버랩 제거
        if remove_overlaps and matches:
            matches = self.segment_matcher.remove_overlaps(matches, mode='source')

        # top_k 제한
        matches = matches[:top_k]

        elapsed_time = time.time() - start_time
        logger.info(f"검색 완료: {len(matches)}개 발견 (소요 시간: {elapsed_time:.2f}초)")

        return matches

    def ensemble_find_segments(
        self,
        algorithm_names: List[str],
        target_audio: np.ndarray,
        source_audio: np.ndarray,
        target_sr: int,
        source_sr: int,
        weights: Optional[List[float]] = None,
        top_k: int = 10,
        voting_method: str = 'weighted_average',
    ) -> List[SimilarityMatch]:
        """
        여러 알고리즘을 앙상블하여 유사 세그먼트를 찾습니다.

        Args:
            algorithm_names: 사용할 알고리즘 이름 리스트
            target_audio: 타겟 오디오
            source_audio: 소스 오디오
            target_sr: 타겟 샘플링 레이트
            source_sr: 소스 샘플링 레이트
            weights: 알고리즘별 가중치 (None인 경우 균등)
            top_k: 반환할 최대 매치 수
            voting_method: 투표 방법 ('weighted_average', 'max', 'min')

        Returns:
            List[SimilarityMatch]: 앙상블 매칭 결과
        """
        if not algorithm_names:
            raise ValueError("알고리즘을 최소 하나 이상 지정해야 합니다.")

        # 가중치 설정
        if weights is None:
            weights = [1.0 / len(algorithm_names)] * len(algorithm_names)
        elif len(weights) != len(algorithm_names):
            raise ValueError("가중치 개수가 알고리즘 개수와 일치해야 합니다.")

        # 가중치 정규화
        weights = np.array(weights)
        weights = weights / np.sum(weights)

        logger.info(
            f"앙상블 검색 시작: {algorithm_names} "
            f"(voting_method={voting_method})"
        )

        # 각 알고리즘으로 매치 찾기
        all_matches_by_algo = []

        for algo_name, weight in zip(algorithm_names, weights):
            matches = self.find_similar_segments(
                algo_name,
                target_audio,
                source_audio,
                target_sr,
                source_sr,
                top_k=top_k * 3,  # 앙상블을 위해 더 많은 후보 확보
                remove_overlaps=False,
            )

            # 가중치 적용
            for match in matches:
                match.metadata = match.metadata or {}
                match.metadata['algorithm'] = algo_name
                match.metadata['weight'] = weight

            all_matches_by_algo.append(matches)

        # 모든 매치 결합
        all_matches = []
        for matches in all_matches_by_algo:
            all_matches.extend(matches)

        # 세그먼트 그룹화 (비슷한 위치의 매치들)
        grouped_matches = self._group_similar_matches(all_matches)

        # 앙상블 스코어 계산
        ensemble_matches = []

        for group in grouped_matches:
            if voting_method == 'weighted_average':
                # 가중 평균
                total_weight = sum([m.metadata.get('weight', 1.0) for m in group])
                ensemble_sim = sum([
                    m.similarity * m.metadata.get('weight', 1.0)
                    for m in group
                ]) / total_weight if total_weight > 0 else 0.0
            elif voting_method == 'max':
                ensemble_sim = max([m.similarity for m in group])
            elif voting_method == 'min':
                ensemble_sim = min([m.similarity for m in group])
            else:
                raise ValueError(f"지원하지 않는 투표 방법: {voting_method}")

            # 대표 매치 선택 (가장 높은 유사도)
            best_match = max(group, key=lambda x: x.similarity)

            ensemble_match = SimilarityMatch(
                target_start=best_match.target_start,
                target_end=best_match.target_end,
                source_start=best_match.source_start,
                source_end=best_match.source_end,
                similarity=ensemble_sim,
                confidence=len(group) / len(algorithm_names),  # 알고리즘 동의율
                metadata={
                    'ensemble': True,
                    'num_votes': len(group),
                    'algorithms': [m.metadata.get('algorithm') for m in group],
                }
            )
            ensemble_matches.append(ensemble_match)

        # 정렬 및 상위 k개 선택
        ensemble_matches.sort(key=lambda x: x.similarity, reverse=True)
        ensemble_matches = ensemble_matches[:top_k]

        logger.info(f"앙상블 검색 완료: {len(ensemble_matches)}개 발견")

        return ensemble_matches

    def _group_similar_matches(
        self,
        matches: List[SimilarityMatch],
        time_tolerance: float = 0.5,
    ) -> List[List[SimilarityMatch]]:
        """
        비슷한 위치의 매치들을 그룹화합니다.

        Args:
            matches: 매칭 결과 리스트
            time_tolerance: 시간 허용 오차 (초)

        Returns:
            List[List[SimilarityMatch]]: 그룹화된 매치 리스트
        """
        if not matches:
            return []

        # 소스 시작 시간 기준 정렬
        sorted_matches = sorted(matches, key=lambda x: x.source_start)

        groups = []
        current_group = [sorted_matches[0]]

        for match in sorted_matches[1:]:
            # 현재 그룹의 평균 위치
            avg_start = np.mean([m.source_start for m in current_group])
            avg_end = np.mean([m.source_end for m in current_group])

            # 새 매치가 현재 그룹과 가까운지 확인
            if (abs(match.source_start - avg_start) < time_tolerance and
                abs(match.source_end - avg_end) < time_tolerance):
                current_group.append(match)
            else:
                groups.append(current_group)
                current_group = [match]

        groups.append(current_group)

        return groups

    def benchmark_algorithms(
        self,
        algorithm_names: Optional[List[str]] = None,
        target_audio: Optional[np.ndarray] = None,
        source_audio: Optional[np.ndarray] = None,
        target_sr: int = 22050,
        source_sr: int = 22050,
        test_duration: float = 3.0,
    ) -> Dict[str, Dict[str, Any]]:
        """
        알고리즘들의 성능을 벤치마크합니다.

        Args:
            algorithm_names: 벤치마크할 알고리즘 이름 (None인 경우 모든 알고리즘)
            target_audio: 테스트용 타겟 오디오
            source_audio: 테스트용 소스 오디오
            target_sr: 타겟 샘플링 레이트
            source_sr: 소스 샘플링 레이트
            test_duration: 테스트용 오디오 생성 시 사용할 길이 (초)

        Returns:
            Dict[str, Dict[str, Any]]: 벤치마크 결과
        """
        if algorithm_names is None:
            algorithm_names = self.list_algorithms()

        # 테스트 오디오 생성 (제공되지 않은 경우)
        if target_audio is None or source_audio is None:
            duration = test_duration
            target_audio = np.random.randn(int(duration * target_sr)).astype(np.float32)
            source_audio = np.random.randn(int(duration * 5 * source_sr)).astype(np.float32)

        logger.info(f"{len(algorithm_names)}개 알고리즘 벤치마크 시작...")

        results = {}

        for name in algorithm_names:
            logger.info(f"벤치마크 중: {name}")

            try:
                start_time = time.time()

                matches = self.find_similar_segments(
                    name,
                    target_audio,
                    source_audio,
                    target_sr,
                    source_sr,
                    top_k=10,
                    remove_overlaps=False,
                )

                elapsed_time = time.time() - start_time

                results[name] = {
                    'num_matches': len(matches),
                    'elapsed_time': elapsed_time,
                    'avg_similarity': np.mean([m.similarity for m in matches]) if matches else 0.0,
                    'max_similarity': max([m.similarity for m in matches]) if matches else 0.0,
                    'min_similarity': min([m.similarity for m in matches]) if matches else 0.0,
                    'success': True,
                }

                logger.info(
                    f"{name}: {len(matches)}개 발견, "
                    f"{elapsed_time:.2f}초 소요"
                )

            except Exception as e:
                logger.error(f"{name} 벤치마크 실패: {str(e)}")
                results[name] = {
                    'success': False,
                    'error': str(e),
                }

        logger.info("벤치마크 완료")

        return results


__all__ = ["AlgorithmManager"]
