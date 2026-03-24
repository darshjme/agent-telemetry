"""Tests for the Span class."""

import time
import pytest
from agent_telemetry import Span


class TestSpanCreation:
    def test_span_has_name(self):
        span = Span("my-op")
        assert span.name == "my-op"

    def test_span_auto_generates_trace_id(self):
        span = Span("op")
        assert span.trace_id
        assert len(span.trace_id) == 36  # UUID4

    def test_span_auto_generates_span_id(self):
        span = Span("op")
        assert span.span_id
        assert len(span.span_id) == 36

    def test_two_spans_have_different_ids(self):
        s1 = Span("op")
        s2 = Span("op")
        assert s1.span_id != s2.span_id
        assert s1.trace_id != s2.trace_id

    def test_span_accepts_custom_trace_id(self):
        span = Span("op", trace_id="fixed-trace-id")
        assert span.trace_id == "fixed-trace-id"

    def test_span_accepts_parent_id(self):
        span = Span("op", parent_id="parent-span-id")
        assert span.parent_id == "parent-span-id"

    def test_span_default_status_is_unset(self):
        span = Span("op")
        assert span.status == "unset"

    def test_span_default_attributes_empty(self):
        span = Span("op")
        assert span.attributes == {}

    def test_span_default_events_empty(self):
        span = Span("op")
        assert span.events == []


class TestSpanLifecycle:
    def test_start_records_start_time(self):
        before = time.time()
        span = Span("op").start()
        after = time.time()
        assert before <= span.start_time <= after

    def test_finish_records_end_time(self):
        span = Span("op").start()
        before_end = time.time()
        span.finish()
        after_end = time.time()
        assert before_end <= span.end_time <= after_end

    def test_finish_sets_status_ok_when_unset(self):
        span = Span("op").start()
        span.finish()
        assert span.status == "ok"

    def test_finish_preserves_error_status(self):
        span = Span("op").start()
        span.status = "error"
        span.finish()
        assert span.status == "error"

    def test_duration_ms_positive_after_finish(self):
        span = Span("op").start()
        time.sleep(0.01)
        span.finish()
        assert span.duration_ms >= 10.0

    def test_duration_ms_zero_before_start(self):
        span = Span("op")
        assert span.duration_ms == 0.0

    def test_duration_ms_live_before_finish(self):
        span = Span("op").start()
        time.sleep(0.005)
        # Not finished yet — should use current time
        assert span.duration_ms > 0


class TestSpanAttributes:
    def test_set_attribute_stores_value(self):
        span = Span("op")
        span.set_attribute("model", "gpt-4o")
        assert span.attributes["model"] == "gpt-4o"

    def test_set_attribute_returns_self(self):
        span = Span("op")
        result = span.set_attribute("k", "v")
        assert result is span

    def test_set_attribute_overwrites_existing(self):
        span = Span("op")
        span.set_attribute("k", "old")
        span.set_attribute("k", "new")
        assert span.attributes["k"] == "new"


class TestSpanEvents:
    def test_add_event_stores_name(self):
        span = Span("op")
        span.add_event("cache-hit")
        assert span.events[0]["name"] == "cache-hit"

    def test_add_event_stores_timestamp(self):
        before = time.time()
        span = Span("op")
        span.add_event("e")
        after = time.time()
        ts = span.events[0]["timestamp"]
        assert before <= ts <= after

    def test_add_event_stores_attributes(self):
        span = Span("op")
        span.add_event("retry", {"attempt": 3})
        assert span.events[0]["attributes"]["attempt"] == 3

    def test_add_event_empty_attributes_by_default(self):
        span = Span("op")
        span.add_event("milestone")
        assert span.events[0]["attributes"] == {}

    def test_add_event_returns_self(self):
        span = Span("op")
        result = span.add_event("e")
        assert result is span


class TestSpanErrors:
    def test_set_error_marks_status_error(self):
        span = Span("op")
        span.set_error(ValueError("bad input"))
        assert span.status == "error"

    def test_set_error_captures_type(self):
        span = Span("op")
        span.set_error(RuntimeError("boom"))
        assert span.attributes["error.type"] == "RuntimeError"

    def test_set_error_captures_message(self):
        span = Span("op")
        span.set_error(ValueError("bad"))
        assert span.attributes["error.message"] == "bad"


class TestSpanContextManager:
    def test_context_manager_starts_and_finishes(self):
        with Span("op") as span:
            pass
        assert span.end_time is not None
        assert span.status == "ok"

    def test_context_manager_captures_exception(self):
        with pytest.raises(ZeroDivisionError):
            with Span("op") as span:
                _ = 1 / 0
        assert span.status == "error"
        assert span.attributes["error.type"] == "ZeroDivisionError"

    def test_context_manager_reraises_exception(self):
        with pytest.raises(ValueError):
            with Span("op"):
                raise ValueError("test")


class TestSpanSerialization:
    def test_to_dict_has_required_keys(self):
        span = Span("op").start()
        span.finish()
        d = span.to_dict()
        for key in ["name", "traceId", "spanId", "parentSpanId", "status", "attributes", "events"]:
            assert key in d

    def test_to_dict_name_matches(self):
        span = Span("router").start()
        span.finish()
        assert span.to_dict()["name"] == "router"

    def test_to_dict_status_is_dict(self):
        span = Span("op").start()
        span.finish()
        assert isinstance(span.to_dict()["status"], dict)
        assert span.to_dict()["status"]["code"] == "ok"
