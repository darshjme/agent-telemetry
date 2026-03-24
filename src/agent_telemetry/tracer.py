"""
Tracer — creates and manages spans with thread-local active span tracking.
"""

from __future__ import annotations

import threading
from contextlib import contextmanager
from typing import Generator

from .span import Span


class Tracer:
    """
    Creates spans and maintains a thread-local active-span stack.

    Usage:
        tracer = Tracer("my-service")

        # Manual
        span = tracer.start_span("router")
        ...
        span.finish()
        tracer.record(span)

        # Context manager (preferred)
        with tracer.with_span("budget-check") as span:
            span.set_attribute("budget", 100)
    """

    def __init__(self, service_name: str) -> None:
        self.service_name = service_name
        self._local = threading.local()
        self._collectors: list = []  # list of TraceCollector instances

    # ------------------------------------------------------------------
    # Span stack helpers (thread-local)
    # ------------------------------------------------------------------

    def _stack(self) -> list[Span]:
        if not hasattr(self._local, "stack"):
            self._local.stack = []
        return self._local.stack

    def get_active_span(self) -> Span | None:
        """Return the innermost active span on this thread, or None."""
        stack = self._stack()
        return stack[-1] if stack else None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start_span(self, name: str, parent: Span | None = None) -> Span:
        """
        Create and start a new span.

        If `parent` is None, the current active span (if any) becomes the
        implicit parent, preserving the trace_id across the call tree.
        """
        active = parent or self.get_active_span()

        span = Span(
            name=name,
            trace_id=active.trace_id if active else None,
            parent_id=active.span_id if active else None,
        )
        span.set_attribute("service.name", self.service_name)
        span.start()
        self._stack().append(span)
        return span

    def record(self, span: Span) -> None:
        """
        Pop span from the active stack and forward to all registered collectors.
        """
        stack = self._stack()
        if span in stack:
            stack.remove(span)
        for collector in self._collectors:
            collector.collect(span)

    def register_collector(self, collector) -> None:
        """Attach a TraceCollector to receive completed spans."""
        self._collectors.append(collector)

    @contextmanager
    def with_span(self, name: str, parent: Span | None = None) -> Generator[Span, None, None]:
        """
        Context manager: starts a span, yields it, then finishes and records it.

        Example:
            with tracer.with_span("llm-call") as span:
                span.set_attribute("model", "gpt-4o")
                result = call_llm(...)
        """
        span = self.start_span(name, parent=parent)
        try:
            yield span
        except Exception as exc:
            span.set_error(exc)
            raise
        finally:
            if span.end_time is None:
                span.finish()
            self.record(span)

    def __repr__(self) -> str:
        return f"Tracer(service={self.service_name!r})"
