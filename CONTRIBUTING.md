# Contributing to agent-telemetry

Thank you for your interest in contributing!

## Development Setup

```bash
git clone https://github.com/darshjme-codes/agent-telemetry
cd agent-telemetry
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running Tests

```bash
python -m pytest tests/ -v
```

All 42 tests must pass before submitting a PR.

## Guidelines

- **Zero dependencies** — stdlib only. No external packages in `dependencies`.
- **Thread safety** — all metric mutations must use `threading.Lock`.
- **Test coverage** — every new feature needs tests. Aim for 100% coverage on new code.
- **Type hints** — use `from __future__ import annotations` and full type hints.
- **Docstrings** — public API must have clear docstrings.

## Submitting a PR

1. Fork the repo
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Write tests first (TDD preferred)
4. Implement the feature
5. Run `python -m pytest tests/ -v` — all must pass
6. Open a PR with a clear description

## Code Style

- PEP 8 compliant
- Max line length: 100 characters
- Use `f-strings` over `.format()`

## Reporting Bugs

Open a GitHub issue with:
- Python version
- Minimal reproducible example
- Expected vs actual behavior
