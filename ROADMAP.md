# 25-Day Build Roadmap

> **Goal**: Build a production-ready AI Inference Gateway with daily GitHub commits.

---

## Week 1: Foundation & Core Gateway

### Day 1 — Project Scaffolding ✅
- Project structure, README, AGENTS.md
- FastAPI app factory, config, logging
- Health endpoints, Docker Compose dev stack
- CI pipeline with GitHub Actions

### Day 2 — Server Foundation
- Middleware stack (request ID, timing, auth)
- Structured logging with context propagation
- Global exception handlers
- Config validation and `.env` support

### Day 3 — Provider Abstraction
- `BaseProvider` ABC with async methods
- Provider registry pattern
- Unified request/response models (OpenAI-compatible)
- Provider capability metadata

### Day 4 — OpenAI Adapter
- `OpenAIProvider` implementing `BaseProvider`
- Chat completions (non-streaming)
- Embeddings endpoint
- Model list mapping

### Day 5 — Anthropic Adapter
- `AnthropicProvider` implementing `BaseProvider`
- Claude message format translation
- Streaming support
- Error translation to gateway format

### Day 6 — Ollama/Local Adapter
- `OllamaProvider` implementing `BaseProvider`
- Local model discovery
- Chat & embeddings via Ollama API
- Health check for local endpoint

### Day 7 — Smart Routing Engine
- Routing strategies: cost, latency, capability
- Fallback chain on provider failure
- Weighted round-robin
- Router middleware integration

---

## Week 2: Caching, Rate Limiting & Streaming

### Day 8 — Redis Semantic Caching
- Sentence-transformers embedding generation
- Redis vector similarity search
- Cache hit/miss metrics
- TTL and invalidation

### Day 9 — Token Bucket Rate Limiting
- Per-user, per-model Redis token buckets
- Sliding window algorithm
- Configurable limits via headers/settings
- 429 responses with Retry-After

### Day 10 — SSE Streaming Proxy
- Server-Sent Events passthrough for all providers
- Chunk normalization to OpenAI format
- Connection management & timeouts
- Client disconnect handling

### Day 11 — WebSocket Streaming
- WebSocket endpoint for chat
- Bidirectional streaming
- Connection pooling to providers
- Heartbeat & reconnection logic

### Day 12 — PostgreSQL + TimescaleDB Schema
- Alembic migrations setup
- Users, API keys, models tables
- Requests log hypertable
- Cost aggregation views

### Day 13 — Cost Tracking Middleware
- Per-request cost calculation
- Token usage recording
- Real-time spend by user/model
- Budget alerts (soft/hard limits)

### Day 14 — Usage Analytics API
- Time-series queries with TimescaleDB
- Dashboard endpoints: daily/weekly/monthly
- Top users, top models
- Export to CSV/JSON

---

## Week 3: Observability, Resilience & Async

### Day 15 — Prometheus Metrics
- Custom metrics: requests, latency, tokens, cost
- Provider-specific counters
- Histogram buckets for p50/p95/p99
- `/metrics` endpoint

### Day 16 — OpenTelemetry Tracing
- OTLP exporter setup
- Trace propagation across providers
- Span annotations for routing decisions
- Jaeger/Tempo integration

### Day 17 — Circuit Breaker
- Per-provider circuit breaker state machine
- Failure threshold & recovery timeout
- Half-open probe requests
- Automatic provider disable/enable

### Day 18 — Redis Streams Queue
- Async job queue with Redis Streams
- Request enqueue on provider failure
- Consumer group for workers
- Dead-letter queue for max retries

### Day 19 — Background Workers
- Async worker pool with asyncio
- Retry with exponential backoff
- Job status tracking API
- Worker metrics & health

### Day 20 — Shadow Mode / Request Replay
- Shadow traffic duplication to new providers
- Replay production traffic for testing
- Diff responses between providers
- A/B model comparison reports

### Day 21 — Grafana Dashboards
- Provisioned dashboards JSON
- Gateway overview: RPS, latency, errors
- Cost dashboard: spend, tokens, users
- Provider health panel

---

## Week 4: Infra, CI/CD & Polish

### Day 22 — Docker & Docker Compose
- Multi-stage Dockerfile optimization
- Docker Compose for production-like local stack
- Health checks & restart policies
- Volume persistence for DB/Redis

### Day 23 — Kubernetes & KEDA
- Deployment, Service, Ingress manifests
- ConfigMap & Secret management
- KEDA ScaledObject for HPA
- Resource limits & probes

### Day 24 — Terraform & GitHub Actions
- Terraform modules: EKS/GKE, RDS/Cloud SQL, ElastiCache
- GitHub Actions: lint → test → build → push
- ArgoCD Application manifests
- GitOps workflow documentation

### Day 25 — Integration Tests & Final Polish
- End-to-end integration test suite
- Load testing with `locust` or `k6`
- Final README with architecture diagrams
- API documentation with examples
- Tag `v0.1.0` release

---

## Daily Commit Checklist

- [ ] Feature implemented and tested
- [ ] `make lint` passes
- [ ] `make test` passes
- [ ] Commit message follows conventional format
- [ ] Pushed to `main` branch
- [ ] CI pipeline green

## Post-25-Day Enhancements (Backlog)

- [ ] Admin UI dashboard (React/Vue)
- [ ] Fine-tuned model deployment pipeline
- [ ] Multi-region gateway federation
- [ ] Persistent chat sessions & history
- [ ] Plugin system for custom middleware
