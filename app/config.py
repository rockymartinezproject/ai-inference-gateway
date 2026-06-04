"""Application configuration via pydantic-settings."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Gateway configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server
    gateway_port: int = Field(default=8080, alias="GATEWAY_PORT")
    gateway_host: str = Field(default="0.0.0.0", alias="GATEWAY_HOST")
    gateway_env: str = Field(default="development", alias="GATEWAY_ENV")
    gateway_workers: int = Field(default=1, alias="GATEWAY_WORKERS")

    # Security
    api_key_header: str = Field(default="X-API-Key", alias="API_KEY_HEADER")
    admin_api_key: str | None = Field(default=None, alias="ADMIN_API_KEY")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/gateway",
        alias="DATABASE_URL",
    )

    # Provider API Keys
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_base_url: str = Field(default="https://api.openai.com/v1", alias="OPENAI_BASE_URL")

    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    anthropic_base_url: str = Field(
        default="https://api.anthropic.com",
        alias="ANTHROPIC_BASE_URL",
    )

    ollama_base_url: str = Field(
        default="http://localhost:11434",
        alias="OLLAMA_BASE_URL",
    )

    # Features
    enable_semantic_cache: bool = Field(default=True, alias="ENABLE_SEMANTIC_CACHE")
    enable_rate_limiting: bool = Field(default=True, alias="ENABLE_RATE_LIMITING")
    enable_circuit_breaker: bool = Field(default=True, alias="ENABLE_CIRCUIT_BREAKER")
    enable_cost_tracking: bool = Field(default=True, alias="ENABLE_COST_TRACKING")
    enable_shadow_mode: bool = Field(default=False, alias="ENABLE_SHADOW_MODE")

    # Cache
    semantic_cache_threshold: float = Field(default=0.95, alias="SEMANTIC_CACHE_THRESHOLD")
    cache_ttl_seconds: int = Field(default=3600, alias="CACHE_TTL_SECONDS")

    # Rate Limiting
    rate_limit_requests_per_minute: int = Field(
        default=60,
        alias="RATE_LIMIT_REQUESTS_PER_MINUTE",
    )
    rate_limit_tokens_per_minute: int = Field(
        default=100000,
        alias="RATE_LIMIT_TOKENS_PER_MINUTE",
    )

    # Observability
    otel_exporter_endpoint: str | None = Field(
        default=None,
        alias="OTEL_EXPORTER_OTLP_ENDPOINT",
    )
    prometheus_port: int = Field(default=9090, alias="PROMETHEUS_PORT")


settings = Settings()
