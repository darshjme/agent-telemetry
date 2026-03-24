# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x     | ✅ Yes     |

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Please email: **darshjme@gmail.com**

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

You will receive a response within 48 hours.

## Scope

`agent-telemetry` is a pure in-process metrics library with no network listeners, no file I/O, and no external dependencies. The attack surface is minimal. Relevant concerns:

- **Thread safety bugs** — race conditions in metric updates
- **Denial of service** — unbounded memory growth in Histogram observation list
- **Integer overflow** — counter values exceeding float precision

## Out of Scope

- Issues in your own application code using this library
- Issues in Python itself or its standard library
