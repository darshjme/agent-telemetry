<div align="center">
<img src="assets/hero.svg" width="100%"/>
</div>

# agent-telemetry

**Lightweight stdlib-only metrics collection and export for LLM agents**

[![PyPI version](https://img.shields.io/pypi/v/agent-telemetry?color=blue&style=flat-square)](https://pypi.org/project/agent-telemetry/) [![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square)](https://python.org) [![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE) [![Tests](https://img.shields.io/badge/tests-passing-brightgreen?style=flat-square)](#)

---

## The Problem

Without telemetry, LLM agents are black boxes. Latency spikes, token overruns, and error-rate degradations are invisible until a user complains. By then, the incident has been running for hours with no trace to diagnose it.

## Installation

```bash
pip install agent-telemetry
```

## Quick Start

```python
from agent_telemetry import TraceCollector, Counter, Gauge

# Initialise
instance = TraceCollector(name="my_agent")

# Use
result = instance.run()
print(result)
```

## API Reference

### `TraceCollector`

```python
class TraceCollector:
    """
    def __init__(self, max_traces: int = 1000) -> None:
    def collect(self, span: Span) -> None:
        """Store a completed span."""
```

### `Counter`

```python
class Counter:
    """Monotonically increasing counter metric."""
    def __init__(self, name: str, labels: Optional[dict] = None) -> None:
    def increment(self, by: float = 1.0) -> None:
    def value(self) -> float:
    def reset(self) -> None:
```

### `Gauge`

```python
class Gauge:
    """Current-value metric that can go up or down."""
    def __init__(self, name: str, labels: Optional[dict] = None) -> None:
    def set(self, value: float) -> None:
    def increment(self, by: float = 1.0) -> None:
    def decrement(self, by: float = 1.0) -> None:
```


## How It Works

### Flow

```mermaid
flowchart LR
    A[User Code] -->|create| B[TraceCollector]
    B -->|configure| C[Counter]
    C -->|execute| D{Success?}
    D -->|yes| E[Return Result]
    D -->|no| F[Error Handler]
    F --> G[Fallback / Retry]
    G --> C
```

### Sequence

```mermaid
sequenceDiagram
    participant App
    participant TraceCollector
    participant Counter

    App->>+TraceCollector: initialise()
    TraceCollector->>+Counter: configure()
    Counter-->>-TraceCollector: ready
    App->>+TraceCollector: run(context)
    TraceCollector->>+Counter: execute(context)
    Counter-->>-TraceCollector: result
    TraceCollector-->>-App: WorkflowResult
```

## Philosophy

> The Gita asks us to observe the field (*kshetra*) without attachment; telemetry is witness-consciousness for code.

---

*Part of the [arsenal](https://github.com/darshjme/arsenal) — production stack for LLM agents.*

*Built by [Darshankumar Joshi](https://github.com/darshjme), Gujarat, India.*
