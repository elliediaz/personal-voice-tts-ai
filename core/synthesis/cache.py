"""
Segment Cache

세그먼트 캐싱 모듈
"""

import logging
from typing import Optional, Tuple, Any
from collections import OrderedDict
import hashlib

import numpy as np

logger = logging.getLogger(__name__)


class SegmentCache:
    """세그먼트 캐시 클래스 (LRU)"""

    def __init__(self, max_size: int = 100):
        """
        Args:
            max_size: 최대 캐시 크기
        """
        self.max_size = max_size
        self.cache = OrderedDict()
        self.hits = 0
        self.misses = 0

        logger.info(f"SegmentCache 초기화: max_size={max_size}")

    def _generate_key(
        self,
        source_file: str,
        start_time: float,
        end_time: float,
    ) -> str:
        """
        캐시 키 생성

        Args:
            source_file: 소스 파일 경로
            start_time: 시작 시간
            end_time: 종료 시간

        Returns:
            캐시 키
        """
        # 파일 경로 + 시간 정보로 해시 생성
        key_str = f"{source_file}:{start_time:.6f}:{end_time:.6f}"
        key_hash = hashlib.md5(key_str.encode()).hexdigest()

        return key_hash

    def get(
        self,
        source_file: str,
        start_time: float,
        end_time: float,
    ) -> Optional[Tuple[np.ndarray, int]]:
        """
        캐시에서 세그먼트 가져오기

        Args:
            source_file: 소스 파일 경로
            start_time: 시작 시간
            end_time: 종료 시간

        Returns:
            (세그먼트, 샘플링 레이트) 또는 None
        """
        key = self._generate_key(source_file, start_time, end_time)

        if key in self.cache:
            # 캐시 히트
            self.hits += 1
            # LRU: 최근 사용으로 이동
            self.cache.move_to_end(key)

            logger.debug(f"캐시 히트: {source_file} [{start_time:.2f}s~{end_time:.2f}s]")

            return self.cache[key]
        else:
            # 캐시 미스
            self.misses += 1

            logger.debug(f"캐시 미스: {source_file} [{start_time:.2f}s~{end_time:.2f}s]")

            return None

    def put(
        self,
        source_file: str,
        start_time: float,
        end_time: float,
        segment: np.ndarray,
        sample_rate: int,
    ):
        """
        캐시에 세그먼트 저장

        Args:
            source_file: 소스 파일 경로
            start_time: 시작 시간
            end_time: 종료 시간
            segment: 세그먼트 데이터
            sample_rate: 샘플링 레이트
        """
        key = self._generate_key(source_file, start_time, end_time)

        # LRU: 오래된 항목 제거
        if len(self.cache) >= self.max_size:
            # 가장 오래된 항목 제거 (FIFO)
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]

            logger.debug(f"캐시 공간 확보: {len(self.cache)}/{self.max_size}")

        # 캐시에 추가
        self.cache[key] = (segment.copy(), sample_rate)

        logger.debug(
            f"캐시 저장: {source_file} [{start_time:.2f}s~{end_time:.2f}s], "
            f"캐시 크기={len(self.cache)}/{self.max_size}"
        )

    def clear(self):
        """캐시 초기화"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0

        logger.info("캐시 초기화 완료")

    def get_stats(self) -> dict:
        """
        캐시 통계 반환

        Returns:
            통계 딕셔너리
        """
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0

        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": total,
            "hit_rate": hit_rate,
        }

    def __len__(self) -> int:
        return len(self.cache)

    def __repr__(self) -> str:
        stats = self.get_stats()
        return (
            f"SegmentCache(size={stats['size']}/{stats['max_size']}, "
            f"hit_rate={stats['hit_rate']:.2%})"
        )
