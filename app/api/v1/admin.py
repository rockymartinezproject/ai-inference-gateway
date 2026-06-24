"""Admin endpoints for gateway management."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.config import settings
from app.core.models import ProviderHealth
from app.dependencies import verify_admin_key
from app.observability.metrics import metrics_response
from app.providers.registry import get_registry

router = APIRouter()


@router.get("/providers/health", response_model=list[ProviderHealth])
async def list_provider_health(
    admin_key: str = Depends(verify_admin_key),  # noqa: ARG001
) -> list[ProviderHealth]:
    """List health status of all configured providers."""
    registry = get_registry()
    return await registry.health_checks()


@router.get("/config")
async def get_config(
    admin_key: str = Depends(verify_admin_key),  # noqa: ARG001
) -> dict:
    """Get current gateway configuration (sensitive values redacted)."""
    return {
        "gateway_env": settings.gateway_env,
        "enable_semantic_cache": settings.enable_semantic_cache,
        "enable_rate_limiting": settings.enable_rate_limiting,
        "enable_circuit_breaker": settings.enable_circuit_breaker,
        "enable_cost_tracking": settings.enable_cost_tracking,
        "enable_shadow_mode": settings.enable_shadow_mode,
    }


@router.get("/metrics")
async def prometheus_metrics(
    admin_key: str = Depends(verify_admin_key),  # noqa: ARG001
) -> bytes:
    """Prometheus metrics endpoint."""
    return metrics_response()
