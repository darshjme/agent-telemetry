# agent-telemetry

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-42%20passed-brightgreen)]()

**Lightweight, stdlib-only metrics collection and export for LLM agents.**

No Prometheus, no OpenTelemetry, no infrastructure required.  
Drop it in, instrument in 5 lines, debug with confidence.

---

## Problem

Production LLM agents are blind without telemetry:

- How many tokens did that agent consume?
- Which model did it call — and how often?
- What's the p95 latency? The failure rate?
- Is the active-agent count climbing under load?

`agent-telemetry` solves this with **zero dependencies**, pure Python stdlib.

---

## Install

```bash
pip install agent-telemetry
```

---

## Quick Start — LLM Token Usage Telemetry

```python
from agent_telemetry import MetricsRegistry

registry = MetricsRegistry()

# --- Define your metrics ---
tokens_used   = registry.counter("llm_tokens_total",  labels={"model": "claude-3-opus"})
api_errors    = registry.counter("llm_errors_total",  labels={"model": "claude-3-opus"})
active_agents = registry.gauge("agents_active")
latency_ms    = registry.histogram("llm_latency_ms")

# --- Simulate an agent run ---
import time

def call_llm(prompt: str) -> dict:
    active_agents.increment()
    t0 = time.monotonic()
    try:
        # ... your LLM call here ...
        response_tokens = 312
        tokens_used.increment(by=response_tokens)
        return {"tokens": response_tokens}
    except Exception as e:
        api_errors.increment()
        raise
    finally:
        elapsed = (time.monotonic() - t0) * 1000
        latency_ms.observe(elapsed)
        active_agents.decrement()

# Run several calls
for prompt in ["Summarize X", "Translate Y", "Classify Z"]:
    call_llm(prompt)

# --- Inspect metrics ---
print(f"Total tokens consumed : {tokens_used.value}")
print(f"Total API errors      : {api_errors.value}")
print(f"Mean latency (ms)     : {latency_ms.mean:.1f}")
print(f"p95  latency (ms)     : {latency_ms.percentile(0.95):.1f}")
print(f"Active agents now     : {active_agents.value}")

# --- Export all metrics as dicts (ship to your log sink) ---
import json
snapshot = registry.collect()
print(json.dumps(snapshot, indent=2, default=str))
```

**Sample output:**

```
Total tokens consumed : 936.0
Total API errors      : 0.0
Mean latency (ms)     : 1.3
p95  latency (ms)     : 2.1
Active agents now     : 0.0
```

---

## API Reference

### `Counter`

Monotonically increasing counter. Use for: token counts, request counts, error counts.

```python
from agent_telemetry import Counter

c = Counter("requests_total", labels={"model": "gpt-4"})
c.increment()          # +1
c.increment(by=150)    # +150
print(c.value)         # float
c.reset()              # back to 0
c.to_dict()            # {"type": "counter", "name": ..., "labels": ..., "value": ...}
```

### `Gauge`

Current value — goes up and down. Use for: active agents, queue depth, memory.

```python
from agent_telemetry import Gauge

g = Gauge("agents_active")
g.set(5)
g.increment()          # 6
g.decrement(by=2)      # 4
print(g.value)
g.to_dict()
```

### `Histogram`

Tracks value distribution. Use for: latency, token-per-request, cost-per-call.

```python
from agent_telemetry import Histogram

h = Histogram("latency_ms", buckets=[10, 50, 100, 500, 1000])
h.observe(73.4)
h.observe(210.1)

print(h.count)              # 2
print(h.sum)                # 283.5
print(h.mean)               # 141.75
print(h.percentile(0.95))   # p95
h.to_dict()                 # full bucket breakdown
```

Default buckets: `[10, 50, 100, 250, 500, 1000, 2500, 5000]`

### `MetricsRegistry`

Central registry — creates, stores, and exports all metrics.

```python
from agent_telemetry import MetricsRegistry

registry = MetricsRegistry()

c = registry.counter("calls")           # get-or-create Counter
g = registry.gauge("workers")           # get-or-create Gauge
h = registry.histogram("latency_ms")    # get-or-create Histogram

all_metrics = registry.collect()        # list[dict]
registry.reset_all()                    # resets all counters
registry.clear()                        # removes all metrics (useful in tests)
```

---

## Export / Integration

`collect()` returns plain Python dicts — ship them anywhere:

```python
import json, logging

snapshot = registry.collect()

# → structured log
logging.info("metrics", extra={"metrics": snapshot})

# → file
with open("metrics.json", "w") as f:
    json.dump(snapshot, f, default=str)

# → your own HTTP sink
import urllib.request, json
req = urllib.request.Request(
    "https://your-sink/metrics",
    data=json.dumps(snapshot).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
urllib.request.urlopen(req)
```

---

## Thread Safety

All metric operations are protected by `threading.Lock`. Safe to use across multiple agent threads.

---

## License

MIT — see [LICENSE](LICENSE).
