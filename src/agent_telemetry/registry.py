"""MetricsRegistry — central store for all metrics."""

from __future__ import annotations

import threading
from typing import Optional

from .metrics import Counter, Gauge, Histogram


class MetricsRegistry:
    """Collects and exports Counter, Gauge, and Histogram metrics."""

    def __init__(self) -> None:
        self._metrics: dict[str, Counter | Gauge | Histogram] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ #
    # Factory helpers                                                      #
    # ------------------------------------------------------------------ #

    def counter(self, name: str, labels: Optional[dict] = None) -> Counter:
        """Get or create a Counter by name."""
        key = self._key(name, labels)
        with self._lock:
            if key not in self._metrics:
                self._metrics[key] = Counter(name, labels)
            existing = self._metrics[key]
        if not isinstance(existing, Counter):
            raise TypeError(f"Metric '{name}' already registered as {type(existing).__name__}")
        return existing

    def gauge(self, name: str, labels: Optional[dict] = None) -> Gauge:
        """Get or create a Gauge by name."""
        key = self._key(name, labels)
        with self._lock:
            if key not in self._metrics:
                self._metrics[key] = Gauge(name, labels)
            existing = self._metrics[key]
        if not isinstance(existing, Gauge):
            raise TypeError(f"Metric '{name}' already registered as {type(existing).__name__}")
        return existing

    def histogram(
        self,
        name: str,
        buckets: Optional[list[float]] = None,
    ) -> Histogram:
        """Get or create a Histogram by name."""
        key = self._key(name, None)
        with self._lock:
            if key not in self._metrics:
                self._metrics[key] = Histogram(name, buckets)
            existing = self._metrics[key]
        if not isinstance(existing, Histogram):
            raise TypeError(f"Metric '{name}' already registered as {type(existing).__name__}")
        return existing

    # ------------------------------------------------------------------ #
    # Export / reset                                                       #
    # ------------------------------------------------------------------ #

    def collect(self) -> list[dict]:
        """Return all registered metrics as a list of dicts."""
        with self._lock:
            metrics = list(self._metrics.values())
        return [m.to_dict() for m in metrics]

    def reset_all(self) -> None:
        """Reset counters; gauges and histograms remain (semantically correct)."""
        with self._lock:
            for m in self._metrics.values():
                if isinstance(m, Counter):
                    m.reset()

    def clear(self) -> None:
        """Remove all registered metrics (useful in tests)."""
        with self._lock:
            self._metrics.clear()

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _key(name: str, labels: Optional[dict]) -> str:
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
