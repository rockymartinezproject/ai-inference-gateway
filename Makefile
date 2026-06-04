.PHONY: all dev test test-integration lint format clean docker-build help migrate-up migrate-down

PYTHON = python
PIP = pip
UVICORN = uvicorn

all: lint test

help:
	@echo "Available targets:"
	@echo "  dev            - Run development server with auto-reload"
	@echo "  test           - Run unit tests"
	@echo "  test-integration - Run integration tests"
	@echo "  lint           - Run ruff linter and mypy type checker"
	@echo "  format         - Format code with black and isort"
	@echo "  clean          - Remove build artifacts"
	@echo "  docker-build   - Build Docker image"
	@echo "  run-prod       - Run production server"
	@echo "  migrate-up     - Run database migrations"
	@echo "  migrate-down   - Rollback database migrations"

dev:
	$(UVICORN) app.main:app --reload --host 0.0.0.0 --port 8080

run-prod:
	$(UVICORN) app.main:app --host 0.0.0.0 --port 8080 --workers 4

test:
	pytest tests/unit -v --cov=app --cov-report=term-missing

test-integration:
	pytest tests/integration -v

lint:
	ruff check app tests
	mypy app

format:
	black app tests
	isort app tests

clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

docker-build:
	docker build -f deployments/docker/Dockerfile -t ai-inference-gateway:latest .

migrate-up:
	alembic upgrade head

migrate-down:
	alembic downgrade -1

install:
	$(PIP) install -r requirements.txt

install-dev:
	$(PIP) install -r requirements.txt -r requirements-dev.txt
