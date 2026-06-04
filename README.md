# AI Inference Gateway

A production-ready unified API gateway for routing requests to multiple LLM providers with load balancing, semantic caching, rate limiting, cost tracking, and comprehensive observability.

## Why This Exists

| Typical GitHub | This Gateway |
|---|---|
| RAG chatbot (single model) | Multi-provider inference with failover |
| Local-only demo | Production deployment patterns |
| No observability | Metrics, tracing, cost tracking |
| Manual scaling | Auto-scaling infrastructure |

## Architecture Overview

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Client    │────▶│   Gateway    │────▶│  Smart Router   │
└─────────────┘     └──────────────┘     └─────────────────┘
                            │                      │
                            ▼                      ▼
                     ┌──────────────┐     ┌─────────────────┐
                     │ Rate Limiter │     │ Provider Pool   │
                     └──────────────┘     │ - OpenAI        │
                     ┌──────────────┐     │ - Anthropic     │
                     │Semantic Cache│     │ - Ollama/Local  │
                     └──────────────┘     └─────────────────┘
                            │
                            ▼
                     ┌──────────────────────────────┐
                     │   Observability & Analytics  │
                     │  Prometheus | Grafana | OTLP  │
                     └──────────────────────────────┘
```

## Tech Stack

| Layer | Technology | Demonstrates |
|---|---|---|
| Gateway | Python (FastAPI) | High-performance async API design |
| Provider routing | Pluggable adapters | Abstraction & extensibility |
| Caching | Redis + embeddings | Cost optimization |
| Queue | Redis Streams | Async processing, backpressure |
| Database | PostgreSQL + TimescaleDB | Time-series analytics |
| Observability | Prometheus + Grafana + OpenTelemetry | Production monitoring |
| Infra | Docker, Kubernetes, Terraform | DevOps maturity |
| CI/CD | GitHub Actions → ArgoCD | GitOps deployment |

## Quick Start

```bash
# Create virtual environment
python -m venv venv && source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run development server
make dev

# Run tests
make test
```

## API Example

```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer $USER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## Key Features

- **Smart Routing** — Route by model capability, cost, or latency; fallback on failure
- **Semantic Caching** — Embed requests, cache similar queries, reduce API spend
- **Token Bucket Rate Limiting** — Per-user, per-model quotas with Redis
- **Streaming Proxy** — SSE/WebSocket passthrough to all providers
- **Cost Tracking Dashboard** — Real-time spend by user, model, time period
- **Circuit Breaker** — Auto-disable failing providers, queue for retry
- **Request Replay / Shadow Mode** — Test new models against production traffic safely
- **Auto-scaling Workers** — KEDA metrics-based HPA

## 25-Day Build Log

| Day | Feature | Status |
|---|---|---|
| 1 | Project scaffolding & architecture | ✅ |
| 2 | FastAPI server setup, config, logging | ✅ |
| 3 | Provider abstraction layer | ✅ |
| 4 | OpenAI adapter | ✅ |
| 5 | Anthropic adapter | ✅ |
| 6 | Ollama/local adapter | ✅ |
| 7 | Smart routing engine | ✅ |
| 8 | Redis semantic caching | ✅ |
| 9 | Token bucket rate limiting | ✅ |
| 10 | SSE streaming proxy | ✅ |
| 11 | WebSocket streaming | ✅ |
| 12 | PostgreSQL + TimescaleDB schema | ✅ |
| 13 | Cost tracking middleware | ✅ |
| 14 | Usage analytics API | ✅ |
| 15 | Prometheus metrics | ✅ |
| 16 | OpenTelemetry tracing | ✅ |
| 17 | Circuit breaker | ✅ |
| 18 | Redis Streams queue | ✅ |
| 19 | Background workers | ✅ |
| 20 | Shadow mode / request replay | ✅ |
| 21 | Grafana dashboards | ✅ |
| 22 | Docker & Docker Compose | ✅ |
| 23 | Kubernetes & KEDA | ✅ |
| 24 | Terraform & GitHub Actions | ✅ |
| 25 | Integration tests & docs | ✅ |

## License

MIT
