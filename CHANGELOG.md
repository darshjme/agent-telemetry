# Changelog

All notable changes to `agent-telemetry` will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] — 2026-03-24

### Added
- `Counter` — monotonically increasing counter with labels, `increment()`, `reset()`, `to_dict()`
- `Gauge` — current-value metric with `set()`, `increment()`, `decrement()`, `to_dict()`
- `Histogram` — value distribution tracking with configurable buckets, `observe()`, `percentile()`, `mean`, `to_dict()`
- `MetricsRegistry` — central registry with `counter()`, `gauge()`, `histogram()`, `collect()`, `reset_all()`, `clear()`
- Thread-safe implementation (all ops protected by `threading.Lock`)
- Zero external dependencies — pure Python stdlib
- Full pytest suite (42 tests)
- MIT license
