# AI Inference Gateway — Agent Guidelines

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entrypoint
│   ├── config.py            # Settings & configuration
│   ├── dependencies.py      # FastAPI dependencies
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py    # API v1 router aggregator
│   │       ├── completions.py
│   │       ├── embeddings.py
│   │       ├── admin.py
│   │       └── health.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── models.py        # Pydantic shared models
│   │   ├── errors.py        # Exception handlers
│   │   └── logging.py       # Structured logging setup
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── base.py          # Abstract provider interface
│   │   ├── openai_provider.py
│   │   ├── anthropic_provider.py
│   │   └── ollama_provider.py
│   ├── router/
│   │   ├── __init__.py
│   │   └── engine.py        # Smart routing logic
│   ├── cache/
│   │   ├── __init__.py
│   │   └── semantic.py      # Semantic caching with embeddings
│   ├── ratelimit/
│   │   ├── __init__.py
│   │   └── token_bucket.py  # Token bucket rate limiting
│   ├── stream/
│   │   ├── __init__.py
│   │   └── proxy.py         # SSE/WebSocket streaming
│   ├── db/
│   │   ├── __init__.py
│   │   ├── session.py       # Async DB session
│   │   └── models.py        # SQLAlchemy models
│   ├── analytics/
│   │   ├── __init__.py
│   │   └── tracker.py       # Cost & usage tracking
│   ├── observability/
│   │   ├── __init__.py
│   │   ├── metrics.py       # Prometheus metrics
│   │   └── tracing.py       # OpenTelemetry setup
│   ├── circuitbreaker/
│   │   ├── __init__.py
│   │   └── breaker.py       # Circuit breaker implementation
│   ├── queue/
│   │   ├── __init__.py
│   │   └── redis_streams.py # Redis Streams queue
│   ├── workers/
│   │   ├── __init__.py
│   │   └── processor.py     # Background job workers
│   └── shadow/
│       ├── __init__.py
│       └── replay.py        # Shadow mode & replay
├── deployments/
│   ├── docker/
│   ├── k8s/
│   └── terraform/
├── dashboards/
│   └── grafana/
├── migrations/              # Alembic database migrations
├── tests/
│   ├── unit/
│   └── integration/
├── scripts/
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── Makefile
└── README.md
```

## Coding Conventions

- **Language**: Python 3.11+
- **Framework**: FastAPI with async/await
- **Formatting**: `black` + `isort`
- **Linting**: `ruff` + `mypy` (strict mode)
- **Testing**: `pytest` with `pytest-asyncio`
- **Config**: `pydantic-settings` with environment variables
- **Logging**: Structured JSON with `structlog`
- **Type hints**: Required on all public functions

## Development Workflow

1. Run `make lint` before committing
2. Run `make test` — all tests must pass
3. Follow conventional commit messages: `feat:`, `fix:`, `docs:`, `refactor:`
4. Push daily — this is a 25-day build challenge

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `GATEWAY_PORT` | `8080` | HTTP server port |
| `GATEWAY_ENV` | `development` | Environment mode |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection |
| `DATABASE_URL` | `postgresql+asyncpg://...` | PostgreSQL connection |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `ANTHROPIC_API_KEY` | — | Anthropic API key |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama endpoint |

## Testing

```bash
# Unit tests
make test

# Integration tests
make test-integration

# Specific test file
pytest tests/unit/test_providers.py -v
```

## Building

```bash
# Development
make dev

# Docker image
make docker-build

# Production with uvicorn
make run-prod
```

## Daily Push Checklist

- [ ] Code passes: `make lint`
- [ ] Tests pass: `make test`
- [ ] Commit message follows convention
- [ ] Pushed to GitHub
