"""Tests for the @traced decorator."""

import pytest
from agent_telemetry import traced, Tracer
from agent_telemetry.collector import TraceCollector
from agent_telemetry.decorator import get_default_collector


def fresh_tracer():
    t = Tracer("test-svc")
    c = TraceCollector()
    t.register_collector(c)
    return t, c


class TestTracedDecorator:
    def test_traced_basic_function_runs(self):
        @traced
        def add(a, b):
            return a + b

        assert add(1, 2) == 3

    def test_traced_creates_span_with_function_name(self):
        tracer, collector = fresh_tracer()

        @traced(tracer=tracer)
        def my_function():
            return 42

        my_function()
        spans = collector.recent(1)
        assert "my_function" in spans[0].name

    def test_traced_custom_name(self):
        tracer, collector = fresh_tracer()

        @traced(name="custom-op", tracer=tracer)
        def my_fn():
            pass

        my_fn()
        spans = collector.recent(1)
        assert spans[0].name == "custom-op"

    def test_traced_with_attributes(self):
        tracer, collector = fresh_tracer()

        @traced(attributes={"component": "llm"}, tracer=tracer)
        def call_llm():
            pass

        call_llm()
        spans = collector.recent(1)
        assert spans[0].attributes.get("component") == "llm"

    def test_traced_captures_exception(self):
        tracer, collector = fresh_tracer()

        @traced(tracer=tracer)
        def boom():
            raise ValueError("test error")

        with pytest.raises(ValueError):
            boom()

        spans = collector.recent(1)
        assert spans[0].status == "error"

    def test_traced_span_is_finished(self):
        tracer, collector = fresh_tracer()

        @traced(tracer=tracer)
        def work():
            pass

        work()
        spans = collector.recent(1)
        assert spans[0].end_time is not None

    def test_traced_preserves_return_value(self):
        tracer, _ = fresh_tracer()

        @traced(tracer=tracer)
        def compute():
            return {"result": 99}

        result = compute()
        assert result == {"result": 99}

    def test_traced_preserves_function_metadata(self):
        @traced
        def my_documented_fn():
            """My docstring."""
            pass

        assert my_documented_fn.__name__ == "my_documented_fn"
        assert my_documented_fn.__doc__ == "My docstring."

    def test_traced_nested_spans_share_trace(self):
        tracer, collector = fresh_tracer()

        @traced(name="outer", tracer=tracer)
        def outer():
            inner()

        @traced(name="inner", tracer=tracer)
        def inner():
            pass

        outer()
        spans = collector.recent(10)
        trace_ids = {s.trace_id for s in spans}
        assert len(trace_ids) == 1  # all same trace
