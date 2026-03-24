"""
TraceCollector — in-memory store for completed spans with query and export.
"""

from __future__ import annotations

import json
import threading
from collections import defaultdict, deque
from typing import Any

from .span import Span


class TraceCollector:
    """
    Thread-safe, bounded in-memory store for completed spans.

    Usage:
        collector = TraceCollector(max_traces=500)
        tracer.register_collector(collector)

        # After running your agent:
        spans = collector.get_trace(trace_id)
        print(collector.stats())
        print(collector.export_json())
    """

    def __init__(self, max_traces: int = 1000) -> None:
        self.max_traces = max_traces
        self._lock = threading.Lock()
        # All spans ordered by insertion (bounded)
        self._spans: deque[Span] = deque(maxlen=max_traces)
        # Fast lookup: trace_id → list of spans
        self._by_trace: dict[str, list[Span]] = defaultdict(list)

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    def collect(self, span: Span) -> None:
        """Store a completed span."""
        with self._lock:
            # If deque is full, the oldest span will be evicted automatically
            # by deque's maxlen. We need to also clean the index.
            if len(self._spans) == self.max_traces:
                oldest = self._spans[0]  # peek (will be dropped)
                tid = oldest.trace_id
                # rebuild index without the oldest span
                # (lazy — only when eviction actually happens)
                self._by_trace[tid] = [
                    s for s in self._by_trace[tid] if s is not oldest
                ]
                if not self._by_trace[tid]:
                    del self._by_trace[tid]

            self._spans.append(span)
            self._by_trace[span.trace_id].append(span)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_trace(self, trace_id: str) -> list[Span]:
        """Return all spans belonging to a trace, ordered by start_time."""
        with self._lock:
            spans = list(self._by_trace.get(trace_id, []))
        spans.sort(key=lambda s: s.start_time)
        return spans

    def recent(self, limit: int = 10) -> list[Span]:
        """Return the most recently collected spans (newest first)."""
        with self._lock:
            all_spans = list(self._spans)
        return list(reversed(all_spans))[:limit]

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_json(self) -> str:
        """
        Export all spans as OTEL-compatible JSON (ResourceSpans format).

        Reference:
          https://opentelemetry.io/docs/specs/otel/protocol/file-exporter/
        """
        with self._lock:
            spans = list(self._spans)

        # Group by trace_id for OTEL ResourceSpans structure
        traces: dict[str, list[dict[str, Any]]] = defaultdict(list)
        service_names: dict[str, str] = {}
        for span in spans:
            traces[span.trace_id].append(span.to_dict())
            svc = span.attributes.get("service.name", "unknown")
            service_names[span.trace_id] = svc

        resource_spans = []
        for trace_id, span_dicts in traces.items():
            resource_spans.append(
                {
                    "resource": {
                        "attributes": {
                            "service.name": service_names.get(trace_id, "unknown")
                        }
                    },
                    "scopeSpans": [
                        {
                            "scope": {"name": "agent-telemetry", "version": "0.1.0"},
                            "spans": span_dicts,
                        }
                    ],
                }
            )

        payload = {"resourceSpans": resource_spans}
        return json.dumps(payload, indent=2)

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def stats(self) -> dict[str, Any]:
        """
        Compute aggregate statistics over collected spans.

        Returns:
            {
                "total_spans": int,
                "total_traces": int,
                "error_rate": float,           # 0.0 – 1.0
                "avg_duration_ms": {           # per operation name
                    "router": 12.4,
                    "llm-call": 230.1,
                    ...
                },
                "error_count": int,
            }
        """
        with self._lock:
            spans = list(self._spans)

        if not spans:
            return {
                "total_spans": 0,
                "total_traces": 0,
                "error_rate": 0.0,
                "error_count": 0,
                "avg_duration_ms": {},
            }

        error_count = sum(1 for s in spans if s.status == "error")
        trace_ids = {s.trace_id for s in spans}

        # Per-operation duration accumulator
        durations: dict[str, list[float]] = defaultdict(list)
        for span in spans:
            if span.end_time is not None:
                durations[span.name].append(span.duration_ms)

        avg_duration_ms = {
            op: sum(vals) / len(vals) for op, vals in durations.items()
        }

        return {
            "total_spans": len(spans),
            "total_traces": len(trace_ids),
            "error_rate": error_count / len(spans),
            "error_count": error_count,
            "avg_duration_ms": avg_duration_ms,
        }

    def clear(self) -> None:
        """Remove all stored spans (useful between tests)."""
        with self._lock:
            self._spans.clear()
            self._by_trace.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._spans)

    def __repr__(self) -> str:
        return f"TraceCollector(spans={len(self)}, max_traces={self.max_traces})"
