"""Tests for Gauge metric."""

from agent_telemetry import Gauge


def test_gauge_default_value():
    g = Gauge("active_agents")
    assert g.value == 0.0


def test_gauge_set():
    g = Gauge("active_agents")
    g.set(5.0)
    assert g.value == 5.0


def test_gauge_set_negative():
    g = Gauge("temperature")
    g.set(-10.0)
    assert g.value == -10.0


def test_gauge_increment():
    g = Gauge("queue_depth")
    g.set(3)
    g.increment()
    assert g.value == 4.0


def test_gauge_increment_by():
    g = Gauge("queue_depth")
    g.increment(by=5.0)
    assert g.value == 5.0


def test_gauge_decrement():
    g = Gauge("queue_depth")
    g.set(10)
    g.decrement()
    assert g.value == 9.0


def test_gauge_decrement_by():
    g = Gauge("queue_depth")
    g.set(10)
    g.decrement(by=4.0)
    assert g.value == 6.0


def test_gauge_to_dict():
    g = Gauge("memory_used", labels={"region": "us-east"})
    g.set(1024.0)
    d = g.to_dict()
    assert d["type"] == "gauge"
    assert d["name"] == "memory_used"
    assert d["value"] == 1024.0
    assert d["labels"] == {"region": "us-east"}
