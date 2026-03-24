"""
agent-telemetry: Lightweight OTEL-compatible tracing for LLM agents.
Pure stdlib, zero dependencies.
"""

from .span import Span
from .tracer import Tracer
from .collector import TraceCollector
from .decorator import traced

__version__ = "0.1.0"
__all__ = ["Span", "Tracer", "TraceCollector", "traced"]
