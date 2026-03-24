# agent-telemetry

**Lightweight, OTEL-compatible tracing for LLM agents. Pure Python stdlib. Zero dependencies.**

```
pip install agent-telemetry
```

## Why?

Production agents make deeply nested calls:

```
router
  ├── budget-check          (2ms)
  ├── llm-call              (230ms)  ← bottleneck
  │     ├── prompt-build    (1ms)
  │     └── openai-api      (228ms)
  ├── tool-execution        (45ms)
  │     ├── web-search      (40ms)
  │     └── result-parse    (5ms)
  └── memory-store          (8ms)
```

Without tracing you can't see this tree, identify bottlenecks, or debug failures.
OpenTelemetry is the standard but its SDK adds 20+ transitive dependencies.
**agent-telemetry** gives you OTEL-compatible spans with **zero deps**, in pure stdlib.

---

## Quick Start

```python
from agent_telemetry import Tracer, TraceCollector, traced

# 1. Create tracer + collector
collector = TraceCollector()
tracer = Tracer("my-agent")
tracer.register_collector(collector)

# 2. Trace a nested agent call tree
with tracer.with_span("router") as root:
    root.set_attribute("input_tokens", 512)

    with tracer.with_span("budget-check") as budget:
        budget.set_attribute("budget_usd", 0.10)
        # ... check budget

    with tracer.with_span("llm-call") as llm:
        llm.set_attribute("model", "gpt-4o")
        llm.add_event("prompt-built", {"tokens": 512})

        with tracer.with_span("openai-api") as api:
            api.set_attribute("endpoint", "chat/completions")
            # ... call OpenAI

    with tracer.with_span("tool-execution") as tool:
        tool.set_attribute("tool", "web_search")
        # ... execute tool

    with tracer.with_span("memory-store") as mem:
        mem.set_attribute("store", "lancedb")
        # ... store to memory

# 3. Inspect results
trace = collector.get_trace(root.trace_id)
for span in trace:
    indent = "  " if span.parent_id else ""
    print(f"{indent}[{span.status}] {span.name}: {span.duration_ms:.1f}ms")
```

Output:
```
[ok] router: 285.3ms
  [ok] budget-check: 1.8ms
  [ok] llm-call: 231.4ms
    [ok] openai-api: 229.1ms
  [ok] tool-execution: 46.2ms
    [ok] web-search: 41.0ms
    [ok] result-parse: 5.1ms
  [ok] memory-store: 8.3ms
```

---

## @traced Decorator

```python
from agent_telemetry import traced

# Bare decorator — uses function name as span name
@traced
def route_request(prompt: str):
    return "llm"

# Custom span name
@traced(name="budget-check")
def check_budget(user_id: str, cost: float) -> bool:
    return True

# Pre-set attributes
@traced(attributes={"component": "llm", "provider": "openai"})
def call_llm(prompt: str) -> str:
    return "response"

# Bring your own tracer (for production use)
tracer = Tracer("my-service")

@traced(tracer=tracer)
def my_function():
    pass
```

---

## Components

### `Span`

```python
from agent_telemetry import Span

with Span("my-op") as span:
    span.set_attribute("key", "value")
    span.add_event("milestone", {"detail": "something happened"})

print(span.duration_ms)   # float ms
print(span.to_dict())     # OTEL-compatible dict
```

### `Tracer`

```python
tracer = Tracer("service-name")

# Manual
span = tracer.start_span("op")
span.set_attribute("x", 1)
span.finish()
tracer.record(span)

# Preferred: context manager
with tracer.with_span("op") as span:
    span.set_attribute("x", 1)

# Active span (thread-local)
active = tracer.get_active_span()
```

### `TraceCollector`

```python
from agent_telemetry import TraceCollector

collector = TraceCollector(max_traces=1000)

# Query
spans = collector.get_trace("trace-uuid")
recent = collector.recent(limit=10)

# Statistics
stats = collector.stats()
# {
#   "total_spans": 42,
#   "total_traces": 5,
#   "error_rate": 0.047,
#   "error_count": 2,
#   "avg_duration_ms": {"router": 12.4, "llm-call": 230.1}
# }

# OTEL-compatible export
json_str = collector.export_json()
```

---

## Error Handling

Exceptions are automatically captured:

```python
with tracer.with_span("risky-op") as span:
    raise ValueError("quota exceeded")

# span.status == "error"
# span.attributes["error.type"] == "ValueError"
# span.attributes["error.message"] == "quota exceeded"
```

---

## OTEL Export Format

`collector.export_json()` produces the OpenTelemetry ResourceSpans JSON format,
compatible with OTEL collectors, Jaeger, Zipkin exporters:

```json
{
  "resourceSpans": [{
    "resource": {"attributes": {"service.name": "my-agent"}},
    "scopeSpans": [{
      "scope": {"name": "agent-telemetry", "version": "0.1.0"},
      "spans": [{
        "name": "router",
        "traceId": "...",
        "spanId": "...",
        "parentSpanId": null,
        "startTimeUnixNano": 1700000000000000000,
        "endTimeUnixNano":   1700000000285000000,
        "durationMs": 285.3,
        "status": {"code": "ok"},
        "attributes": {"service.name": "my-agent", "input_tokens": 512},
        "events": []
      }]
    }]
  }]
}
```

---

## Thread Safety

All `TraceCollector` operations are protected by a `threading.Lock`.
`Tracer` uses `threading.local` for the active-span stack — each thread
has its own independent call stack, making `Tracer` safe to share across threads.

---

## License

MIT
