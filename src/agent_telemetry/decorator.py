"""
@traced — decorator for automatic span creation around functions.

Supports three usage patterns:
    @traced
    @traced(name="custom-name")
    @traced(attributes={"component": "llm"})
"""

from __future__ import annotations

import functools
from typing import Any, Callable

from .span import Span
from .tracer import Tracer

# Module-level default tracer (used when @traced is applied without a tracer)
_default_tracer: Tracer | None = None
_default_collector = None


def _get_default_tracer() -> Tracer:
    global _default_tracer, _default_collector
    if _default_tracer is None:
        from .collector import TraceCollector

        _default_tracer = Tracer("agent-telemetry-default")
        _default_collector = TraceCollector()
        _default_tracer.register_collector(_default_collector)
    return _default_tracer


def get_default_collector():
    _get_default_tracer()  # ensure initialised
    return _default_collector


def traced(
    func: Callable | None = None,
    *,
    name: str | None = None,
    attributes: dict[str, Any] | None = None,
    tracer: Tracer | None = None,
) -> Callable:
    """
    Decorator that wraps a function in a span.

    Usage:
        @traced
        def my_function(): ...

        @traced(name="custom-name")
        def my_function(): ...

        @traced(attributes={"component": "llm"}, tracer=my_tracer)
        def my_function(): ...
    """

    def decorator(fn: Callable) -> Callable:
        span_name = name or fn.__qualname__

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            t = tracer or _get_default_tracer()
            with t.with_span(span_name) as span:
                if attributes:
                    for k, v in attributes.items():
                        span.set_attribute(k, v)
                return fn(*args, **kwargs)

        # Async support
        import asyncio

        if asyncio.iscoroutinefunction(fn):

            @functools.wraps(fn)
            async def async_wrapper(*args, **kwargs):
                t = tracer or _get_default_tracer()
                with t.with_span(span_name) as span:
                    if attributes:
                        for k, v in attributes.items():
                            span.set_attribute(k, v)
                    return await fn(*args, **kwargs)

            return async_wrapper

        return wrapper

    # Allow both @traced and @traced(...) usage
    if func is not None:
        # Called as @traced (no parentheses)
        return decorator(func)
    # Called as @traced(...) (with arguments)
    return decorator
