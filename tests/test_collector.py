"""Tests for TraceCollector."""

import json
import time
import pytest
from agent_telemetry import Tracer, Span
from agent_telemetry.collector import TraceCollector


def make_finished_span(name="op", status="ok", trace_id=None, duration_sleep=0.0):
    span = Span(name, trace_id=trace_id)
    span.start()
    if duration_sleep:
        time.sleep(duration_sleep)
    span.finish()
    if status == "error":
        span.status = "error"
    return span


class TestCollectorBasic:
    def test_collect_stores_span(self):
        c = TraceCollector()
        span = make_finished_span()
        c.collect(span)
        assert len(c) == 1

    def test_get_trace_returns_correct_spans(self):
        c = TraceCollector()
        tid = "trace-abc"
        s1 = make_finished_span("op1", trace_id=tid)
        s2 = make_finished_span("op2", trace_id=tid)
        s3 = make_finished_span("op3")  # different trace
        c.collect(s1)
        c.collect(s2)
        c.collect(s3)
        result = c.get_trace(tid)
        assert len(result) == 2
        names = {s.name for s in result}
        assert names == {"op1", "op2"}

    def test_get_trace_returns_empty_for_unknown(self):
        c = TraceCollector()
        assert c.get_trace("nonexistent") == []

    def test_recent_returns_newest_first(self):
        c = TraceCollector()
        for i in range(5):
            c.collect(make_finished_span(f"op{i}"))
        recent = c.recent(3)
        assert len(recent) == 3
        # newest should be op4
        assert recent[0].name == "op4"

    def test_recent_limit_respected(self):
        c = TraceCollector()
        for i in range(20):
            c.collect(make_finished_span(f"op{i}"))
        assert len(c.recent(5)) == 5

    def test_max_traces_evicts_oldest(self):
        c = TraceCollector(max_traces=3)
        for i in range(5):
            c.collect(make_finished_span(f"op{i}"))
        assert len(c) == 3


class TestCollectorStats:
    def test_stats_empty_collector(self):
        c = TraceCollector()
        s = c.stats()
        assert s["total_spans"] == 0
        assert s["total_traces"] == 0
        assert s["error_rate"] == 0.0

    def test_stats_total_spans(self):
        c = TraceCollector()
        c.collect(make_finished_span())
        c.collect(make_finished_span())
        assert c.stats()["total_spans"] == 2

    def test_stats_error_rate(self):
        c = TraceCollector()
        c.collect(make_finished_span(status="ok"))
        c.collect(make_finished_span(status="ok"))
        c.collect(make_finished_span(status="error"))
        s = c.stats()
        assert abs(s["error_rate"] - 1 / 3) < 0.001

    def test_stats_avg_duration_by_name(self):
        c = TraceCollector()
        c.collect(make_finished_span("router"))
        c.collect(make_finished_span("router"))
        c.collect(make_finished_span("llm-call"))
        s = c.stats()
        assert "router" in s["avg_duration_ms"]
        assert "llm-call" in s["avg_duration_ms"]

    def test_stats_error_count(self):
        c = TraceCollector()
        c.collect(make_finished_span(status="error"))
        c.collect(make_finished_span(status="ok"))
        assert c.stats()["error_count"] == 1


class TestCollectorExport:
    def test_export_json_is_valid_json(self):
        c = TraceCollector()
        c.collect(make_finished_span())
        data = json.loads(c.export_json())
        assert "resourceSpans" in data

    def test_export_json_contains_span(self):
        c = TraceCollector()
        span = make_finished_span("router")
        c.collect(span)
        data = json.loads(c.export_json())
        spans = data["resourceSpans"][0]["scopeSpans"][0]["spans"]
        assert spans[0]["name"] == "router"

    def test_export_json_scope_name(self):
        c = TraceCollector()
        c.collect(make_finished_span())
        data = json.loads(c.export_json())
        scope = data["resourceSpans"][0]["scopeSpans"][0]["scope"]
        assert scope["name"] == "agent-telemetry"

    def test_clear_removes_all_spans(self):
        c = TraceCollector()
        c.collect(make_finished_span())
        c.clear()
        assert len(c) == 0
