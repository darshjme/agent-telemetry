# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅        |

## Reporting a Vulnerability

Please **do not** open public GitHub issues for security vulnerabilities.

Report privately via email to: security@example.com

Include:
- Description of the vulnerability
- Steps to reproduce
- Impact assessment
- Suggested fix (if any)

We will respond within 72 hours and aim to release a patch within 14 days.

## Scope

agent-telemetry is a pure-stdlib observability library. The main attack surface is:

- **TraceCollector** — unbounded growth if `max_traces` is set very high; use a reasonable limit in production
- **export_json** — span attributes are user-supplied; sanitize before forwarding to external collectors
- **@traced attributes** — do not log sensitive data (API keys, PII) as span attributes
