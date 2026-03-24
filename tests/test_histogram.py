"""Tests for Histogram metric."""

import math
import pytest
from agent_telemetry import Histogram


def test_histogram_empty_count():
    h = Histogram("latency_ms")
    assert h.count == 0


def test_histogram_empty_sum():
    h = Histogram("latency_ms")
    assert h.sum == 0.0


def test_histogram_empty_mean():
    h = Histogram("latency_ms")
    assert h.mean == 0.0


def test_histogram_observe_count():
    h = Histogram("latency_ms")
    h.observe(100)
    h.observe(200)
    assert h.count == 2


def test_histogram_observe_sum():
    h = Histogram("latency_ms")
    h.observe(100.0)
    h.observe(200.0)
    assert h.sum == 300.0


def test_histogram_mean():
    h = Histogram("latency_ms")
    h.observe(100)
    h.observe(300)
    assert h.mean == pytest.approx(200.0)


def test_histogram_percentile_p50():
    h = Histogram("latency_ms")
    for v in [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
        h.observe(v)
    assert h.percentile(0.5) == 50.0


def test_histogram_percentile_p95():
    h = Histogram("latency_ms")
    for v in range(1, 101):
        h.observe(float(v))
    assert h.percentile(0.95) == 95.0


def test_histogram_percentile_p100():
    h = Histogram("latency_ms")
    h.observe(42.0)
    assert h.percentile(1.0) == 42.0


def test_histogram_percentile_invalid_raises():
    h = Histogram("latency_ms")
    with pytest.raises(ValueError):
        h.percentile(0.0)
    with pytest.raises(ValueError):
        h.percentile(1.5)


def test_histogram_percentile_empty():
    h = Histogram("latency_ms")
    assert h.percentile(0.95) == 0.0


def test_histogram_custom_buckets():
    h = Histogram("custom", buckets=[1, 5, 10])
    h.observe(3)
    d = h.to_dict()
    les = [b["le"] for b in d["buckets"]]
    assert 1 in les and 5 in les and 10 in les
    assert math.inf in les  # auto-appended


def test_histogram_to_dict_structure():
    h = Histogram("response_time")
    h.observe(75.0)
    d = h.to_dict()
    assert d["type"] == "histogram"
    assert d["name"] == "response_time"
    assert d["count"] == 1
    assert d["sum"] == 75.0
    assert "buckets" in d
    assert isinstance(d["buckets"], list)
