# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please open a private
security advisory via GitHub or email the maintainers directly.

Please do not open public issues for security bugs.

## Security Practices

- API keys are never logged or returned in responses.
- Secrets are mounted via Kubernetes Secrets or environment variables.
- Dependencies are audited weekly via `pip-audit`.
- Code is scanned with `bandit` on every push.
