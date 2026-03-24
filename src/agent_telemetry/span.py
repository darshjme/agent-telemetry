"""
Span — represents a single timed operation in a trace tree.
OTEL-compatible fields and serialization.
"""

from __future__ import annotations

import time
import uuid
from typing import Any


class Span:
    """
    A timed operation unit. Compatible with OpenTelemetry span structure.

    Usage:
        span = Span("my-op")
        span.start()
        span.set_attribute("component", "llm")
        span.finish()

        # Or as context manager:
        with Span("my-op") as span:
            span.set_attribute("model", "gpt-4")
    """

    def __init__(
        self,
        name: str,
        trace_id: str | None = None,
        parent_id: str | None = None,
    ) -> None:
        self.name: str = name
        self.trace_id: str = trace_id or str(uuid.uuid4())
        self.span_id: str = str(uuid.uuid4())
        self.parent_id: str | None = parent_id
        self.start_time: float = 0.0
        self.end_time: float | None = None
        self.status: str = "unset"  # "ok" | "error" | "unset"
        self.attributes: dict[str, Any] = {}
        self.events: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> "Span":
        """Record start timestamp."""
        self.start_time = time.time()
        return self

    def finish(self) -> "Span":
        """Record end timestamp; mark status ok if still unset."""
        self.end_time = time.time()
        if self.status == "unset":
            self.status = "ok"
        return self

    # ------------------------------------------------------------------
    # Attributes & events
    # ------------------------------------------------------------------

    def set_attribute(self, key: str, value: Any) -> "Span":
        """Attach an arbitrary key/value attribute."""
        self.attributes[key] = value
        return self

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> "Span":
        """Record a named event (milestone) within this span."""
        self.events.append(
            {
                "name": name,
                "timestamp": time.time(),
                "attributes": attributes or {},
            }
        )
        return self

    def set_error(self, error: Exception) -> "Span":
        """Mark span as errored and capture exception metadata."""
        self.status = "error"
        self.attributes["error.type"] = type(error).__name__
        self.attributes["error.message"] = str(error)
        return self

    # ------------------------------------------------------------------
    # Computed properties
    # ------------------------------------------------------------------

    @property
    def duration_ms(self) -> float:
        """Elapsed time in milliseconds. Uses current time if not finished."""
        end = self.end_time if self.end_time is not None else time.time()
        if self.start_time == 0.0:
            return 0.0
        return (end - self.start_time) * 1000.0

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "Span":
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_val is not None:
            self.set_error(exc_val)
        self.finish()
        return False  # do not suppress exceptions

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """
        Export span as an OTEL-compatible dict.

        Maps to the OTEL JSON trace format:
        https://opentelemetry.io/docs/specs/otel/protocol/file-exporter/
        """
        return {
            "name": self.name,
            "traceId": self.trace_id,
            "spanId": self.span_id,
            "parentSpanId": self.parent_id,
            "startTimeUnixNano": int(self.start_time * 1e9),
            "endTimeUnixNano": int(self.end_time * 1e9) if self.end_time else None,
            "durationMs": self.duration_ms,
            "status": {"code": self.status},
            "attributes": self.attributes,
            "events": self.events,
        }

    def __repr__(self) -> str:
        return (
            f"Span(name={self.name!r}, status={self.status!r}, "
            f"duration_ms={self.duration_ms:.2f})"
        )
