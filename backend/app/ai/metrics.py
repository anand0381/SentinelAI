from collections import Counter
from dataclasses import dataclass, field
from threading import Lock

from app.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class AIMetricsSnapshot:
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    retry_count: int = 0
    cache_hit_count: int = 0
    cache_miss_count: int = 0
    quota_failures: int = 0
    response_times_ms: list[int] = field(default_factory=list)
    model_usage: Counter[str] = field(default_factory=Counter)


class AIMetrics:
    _snapshot = AIMetricsSnapshot()
    _lock = Lock()

    @classmethod
    def record_cache_hit(cls) -> None:
        with cls._lock:
            cls._snapshot.cache_hit_count += 1
        cls.log_summary()

    @classmethod
    def record_cache_miss(cls) -> None:
        with cls._lock:
            cls._snapshot.cache_miss_count += 1

    @classmethod
    def record_request_start(cls) -> None:
        with cls._lock:
            cls._snapshot.total_requests += 1

    @classmethod
    def record_success(cls, model: str, duration_ms: int) -> None:
        with cls._lock:
            cls._snapshot.successful_requests += 1
            cls._snapshot.response_times_ms.append(duration_ms)
            cls._snapshot.model_usage[model] += 1
        cls.log_summary()

    @classmethod
    def record_failure(cls, quota_exhausted: bool = False) -> None:
        with cls._lock:
            cls._snapshot.failed_requests += 1
            if quota_exhausted:
                cls._snapshot.quota_failures += 1
        cls.log_summary()

    @classmethod
    def record_retry(cls) -> None:
        with cls._lock:
            cls._snapshot.retry_count += 1

    @classmethod
    def log_summary(cls) -> None:
        with cls._lock:
            times = cls._snapshot.response_times_ms
            average_ms = int(sum(times) / len(times)) if times else 0
            minimum_ms = min(times) if times else 0
            maximum_ms = max(times) if times else 0
            model_usage = dict(cls._snapshot.model_usage)
            logger.info(
                "AI metrics | total=%s success=%s failed=%s retries=%s "
                "cache_hits=%s cache_misses=%s quota_failures=%s "
                "avg_ms=%s min_ms=%s max_ms=%s model_usage=%s",
                cls._snapshot.total_requests,
                cls._snapshot.successful_requests,
                cls._snapshot.failed_requests,
                cls._snapshot.retry_count,
                cls._snapshot.cache_hit_count,
                cls._snapshot.cache_miss_count,
                cls._snapshot.quota_failures,
                average_ms,
                minimum_ms,
                maximum_ms,
                model_usage,
            )

