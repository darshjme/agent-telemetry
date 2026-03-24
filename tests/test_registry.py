"""Tests for MetricsRegistry."""

import pytest
from agent_telemetry import Counter, Gauge, Histogram, MetricsRegistry


@pytest.fixture
def registry():
    r = MetricsRegistry()
    return r


def test_registry_counter_create(registry):
    c = registry.counter("requests")
    assert isinstance(c, Counter)


def test_registry_counter_idempotent(registry):
    c1 = registry.counter("requests")
    c2 = registry.counter("requests")
    assert c1 is c2


def test_registry_gauge_create(registry):
    g = registry.gauge("active")
    assert isinstance(g, Gauge)


def test_registry_gauge_idempotent(registry):
    g1 = registry.gauge("active")
    g2 = registry.gauge("active")
    assert g1 is g2


def test_registry_histogram_create(registry):
    h = registry.histogram("latency")
    assert isinstance(h, Histogram)


def test_registry_histogram_idempotent(registry):
    h1 = registry.histogram("latency")
    h2 = registry.histogram("latency")
    assert h1 is h2


def test_registry_collect_returns_list(registry):
    registry.counter("calls").increment(5)
    registry.gauge("workers").set(3)
    result = registry.collect()
    assert isinstance(result, list)
    assert len(result) == 2


def test_registry_collect_dict_types(registry):
    registry.counter("x")
    registry.gauge("y")
    registry.histogram("z")
    types = {d["type"] for d in registry.collect()}
    assert types == {"counter", "gauge", "histogram"}


def test_registry_reset_all_resets_counters(registry):
    c = registry.counter("calls")
    c.increment(99)
    registry.reset_all()
    assert c.value == 0.0


def test_registry_reset_all_preserves_gauge(registry):
    g = registry.gauge("workers")
    g.set(7)
    registry.reset_all()
    assert g.value == 7.0  # gauges not reset by reset_all


def test_registry_type_conflict_raises(registry):
    registry.counter("conflict")
    with pytest.raises(TypeError):
        registry.gauge("conflict")


def test_registry_counter_with_labels(registry):
    c = registry.counter("tokens", labels={"model": "claude-3"})
    c.increment(500)
    result = registry.collect()
    assert any(d["value"] == 500.0 for d in result)


def test_registry_clear(registry):
    registry.counter("temp").increment(1)
    registry.clear()
    assert registry.collect() == []
