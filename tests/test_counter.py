"""Tests for Counter metric."""

import pytest
from agent_telemetry import Counter


def test_counter_default_value():
    c = Counter("requests")
    assert c.value == 0.0


def test_counter_increment_default():
    c = Counter("requests")
    c.increment()
    assert c.value == 1.0


def test_counter_increment_by():
    c = Counter("tokens")
    c.increment(by=150.0)
    assert c.value == 150.0


def test_counter_multiple_increments():
    c = Counter("calls")
    c.increment(10)
    c.increment(5)
    assert c.value == 15.0


def test_counter_reset():
    c = Counter("calls")
    c.increment(42)
    c.reset()
    assert c.value == 0.0


def test_counter_negative_raises():
    c = Counter("calls")
    with pytest.raises(ValueError):
        c.increment(-1)


def test_counter_to_dict():
    c = Counter("api_calls", labels={"model": "gpt-4"})
    c.increment(3)
    d = c.to_dict()
    assert d["type"] == "counter"
    assert d["name"] == "api_calls"
    assert d["value"] == 3.0
    assert d["labels"] == {"model": "gpt-4"}


def test_counter_labels_default_empty():
    c = Counter("x")
    assert c.labels == {}
