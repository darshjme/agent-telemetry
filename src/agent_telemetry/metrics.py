"""Core metric types: Counter, Gauge, Histogram."""

from __future__ import annotations

import bisect
import math
import threading
import time
from typing import Optional


_DEFAULT_BUCKETS: list[float] = [10, 50, 100, 250, 500, 1000, 2500, 5000]


class Counter:
    """Monotonically increasing counter metric."""

    def __init__(self, name: str, labels: Optional[dict] = None) -> None:
        self.name = name
        self.labels: dict = labels or {}
        self._value: float = 0.0
        self._lock = threading.Lock()
        self._created_at: float = time.time()

    def increment(self, by: float = 1.0) -> None:
        if by < 0:
            raise ValueError("Counter can only be incremented by non-negative values.")
        with self._lock:
            self._value += by

    @property
    def value(self) -> float:
        with self._lock:
            return self._value

    def reset(self) -> None:
        with self._lock:
            self._value = 0.0

    def to_dict(self) -> dict:
        return {
            "type": "counter",
            "name": self.name,
            "labels": dict(self.labels),
            "value": self.value,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"Counter(name={self.name!r}, value={self.value})"


class Gauge:
    """Current-value metric that can go up or down."""

    def __init__(self, name: str, labels: Optional[dict] = None) -> None:
        self.name = name
        self.labels: dict = labels or {}
        self._value: float = 0.0
        self._lock = threading.Lock()

    def set(self, value: float) -> None:
        with self._lock:
            self._value = float(value)

    def increment(self, by: float = 1.0) -> None:
        with self._lock:
            self._value += by

    def decrement(self, by: float = 1.0) -> None:
        with self._lock:
            self._value -= by

    @property
    def value(self) -> float:
        with self._lock:
            return self._value

    def to_dict(self) -> dict:
        return {
            "type": "gauge",
            "name": self.name,
            "labels": dict(self.labels),
            "value": self.value,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"Gauge(name={self.name!r}, value={self.value})"


class Histogram:
    """Tracks distribution of observed values with configurable buckets."""

    def __init__(
        self,
        name: str,
        buckets: Optional[list[float]] = None,
    ) -> None:
        self.name = name
        raw = list(buckets) if buckets is not None else list(_DEFAULT_BUCKETS)
        raw = sorted(raw)
        if not raw or raw[-1] != math.inf:
            raw.append(math.inf)
        self._buckets: list[float] = raw
        self._counts: list[int] = [0] * len(self._buckets)
        self._sum: float = 0.0
        self._count: int = 0
        self._observations: list[float] = []
        self._lock = threading.Lock()

    def observe(self, value: float) -> None:
        with self._lock:
            self._count += 1
            self._sum += value
            self._observations.append(value)
            idx = bisect.bisect_left(self._buckets, value)
            for i in range(idx, len(self._buckets)):
                self._counts[i] += 1

    @property
    def count(self) -> int:
        with self._lock:
            return self._count

    @property
    def sum(self) -> float:
        with self._lock:
            return self._sum

    @property
    def mean(self) -> float:
        with self._lock:
            if self._count == 0:
                return 0.0
            return self._sum / self._count

    def percentile(self, p: float) -> float:
        """Return the p-th percentile (0 < p <= 1), e.g. p=0.95 for p95."""
        if not 0 < p <= 1:
            raise ValueError("p must be in (0, 1]")
        with self._lock:
            if not self._observations:
                return 0.0
            sorted_obs = sorted(self._observations)
            idx = math.ceil(p * len(sorted_obs)) - 1
            return sorted_obs[max(0, idx)]

    def to_dict(self) -> dict:
        with self._lock:
            bucket_data = [
                {"le": b, "count": c}
                for b, c in zip(self._buckets, self._counts)
            ]
            return {
                "type": "histogram",
                "name": self.name,
                "count": self._count,
                "sum": self._sum,
                "mean": self._sum / self._count if self._count else 0.0,
                "buckets": bucket_data,
            }

    def __repr__(self) -> str:  # pragma: no cover
        return f"Histogram(name={self.name!r}, count={self.count}, mean={self.mean:.2f})"
