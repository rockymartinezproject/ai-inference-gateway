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
# Clone and setup
 git clone https://github.com/rockymartinezproject/ai-inference-gateway.git
 cd ai-inference-gateway

# Create virtual environment
python -m venv venv && source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run development server
make dev

# Run tests
make test
```

## Docker Compose

```bash
# Development stack with Redis, TimescaleDB, Prometheus, Grafana
make dev-up

# Production-like stack
 docker compose -f deployments/docker/docker-compose.prod.yml up -d
```

## API Example

```bash
# List available models
curl http://localhost:8080/v1/models \
  -H "X-API-Key: your-key"

# Chat completion
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer $USER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# Streaming
curl -X POST http://localhost:8080/v1/chat/completions/stream \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "Hello!"}],
    "stream": true
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

## Deployment

### Kubernetes

```bash
# Apply all manifests
kubectl apply -f deployments/k8s/

# Or use ArgoCD for GitOps
kubectl apply -f deployments/k8s/argocd-application.yml
```

### Terraform (AWS)

```bash
cd deployments/terraform
terraform init
terraform plan -var="db_password=your-password"
terraform apply
```

## Build Log

| Day | Feature | Status |
|---|---|---|
| 1 | Project scaffolding & architecture | ✅ |
| 2 | FastAPI server setup with middleware | ✅ |
| 3 | Provider abstraction layer & registry | ✅ |
| 4 | OpenAI adapter with HTTP client | ✅ |
| 5 | Anthropic adapter with Claude translation | ✅ |
| 6 | Ollama/local adapter | ✅ |
| 7 | Smart routing engine with fallback | ✅ |
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
| 25 | Integration tests & v0.1.0 release | ✅ |
| 26 | Real provider integration tests | ✅ |
| 27 | Load testing with k6 | ✅ |
| 28 | Plugin system for custom middleware | ✅ |
| 29 | Persistent chat sessions & history | ✅ |
| 30 | Admin UI dashboard (React/Vite) | ✅ |

## Testing

```bash
# Unit tests
make test

# Integration tests
make test-integration

# Real-provider integration tests (requires API keys)
make test-integration-real

# Load tests (requires k6 and a running gateway)
make test-load

# Specific test file
pytest tests/unit/test_router.py -v
```

## License

MIT
