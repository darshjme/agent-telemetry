# Contributing

## Setup

```bash
git clone https://github.com/example/agent-telemetry
cd agent-telemetry
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Running Tests

```bash
python -m pytest tests/ -v
```

All 71 tests must pass before submitting a PR.

## Guidelines

- Zero dependencies — any new feature must use stdlib only
- Every public method needs a test
- Follow existing code style (no linter required, keep it readable)
- Keep `to_dict()` output OTEL-compatible

## Submitting a PR

1. Fork and branch from `main`
2. Write tests first (TDD preferred)
3. Ensure all tests pass
4. Update `CHANGELOG.md`
5. Open a PR with a clear description
