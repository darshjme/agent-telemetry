"""Tests for the Tracer class."""

import pytest
from agent_telemetry import Tracer, Span
from agent_telemetry.collector import TraceCollector


class TestTracerBasic:
    def test_tracer_has_service_name(self):
        tracer = Tracer("my-service")
        assert tracer.service_name == "my-service"

    def test_start_span_returns_started_span(self):
        tracer = Tracer("svc")
        span = tracer.start_span("op")
        assert span.start_time > 0
        assert span.name == "op"

    def test_start_span_sets_service_attribute(self):
        tracer = Tracer("my-service")
        span = tracer.start_span("op")
        assert span.attributes.get("service.name") == "my-service"

    def test_start_span_no_parent_has_no_parent_id(self):
        tracer = Tracer("svc")
        span = tracer.start_span("root")
        assert span.parent_id is None


class TestTracerActiveSpan:
    def test_get_active_span_none_initially(self):
        tracer = Tracer("svc")
        assert tracer.get_active_span() is None

    def test_get_active_span_returns_started_span(self):
        tracer = Tracer("svc")
        span = tracer.start_span("root")
        assert tracer.get_active_span() is span

    def test_record_removes_span_from_active_stack(self):
        tracer = Tracer("svc")
        span = tracer.start_span("root")
        span.finish()
        tracer.record(span)
        assert tracer.get_active_span() is None

    def test_nested_spans_share_trace_id(self):
        tracer = Tracer("svc")
        parent = tracer.start_span("parent")
        child = tracer.start_span("child")
        assert parent.trace_id == child.trace_id

    def test_nested_spans_parent_child_link(self):
        tracer = Tracer("svc")
        parent = tracer.start_span("parent")
        child = tracer.start_span("child")
        assert child.parent_id == parent.span_id


class TestTracerWithSpan:
    def test_with_span_starts_and_finishes(self):
        tracer = Tracer("svc")
        with tracer.with_span("op") as span:
            assert span.start_time > 0
        assert span.end_time is not None

    def test_with_span_records_to_collector(self):
        collector = TraceCollector()
        tracer = Tracer("svc")
        tracer.register_collector(collector)
        with tracer.with_span("op"):
            pass
        assert len(collector) == 1

    def test_with_span_captures_error(self):
        tracer = Tracer("svc")
        collector = TraceCollector()
        tracer.register_collector(collector)
        with pytest.raises(RuntimeError):
            with tracer.with_span("op"):
                raise RuntimeError("fail")
        spans = collector.recent(1)
        assert spans[0].status == "error"

    def test_with_span_active_span_cleared_after(self):
        tracer = Tracer("svc")
        with tracer.with_span("op"):
            pass
        assert tracer.get_active_span() is None


class TestTracerCollector:
    def test_register_multiple_collectors(self):
        c1 = TraceCollector()
        c2 = TraceCollector()
        tracer = Tracer("svc")
        tracer.register_collector(c1)
        tracer.register_collector(c2)
        with tracer.with_span("op"):
            pass
        assert len(c1) == 1
        assert len(c2) == 1
