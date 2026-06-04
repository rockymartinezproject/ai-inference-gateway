"""Admin endpoints for gateway management."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import Settings, settings
from app.core.models import ProviderHealth

router = APIRouter()


def verify_admin_key(api_key: str | None = None) -> None:
    """Verify admin API key."""
    if not settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Admin API key not configured",
        )
    if api_key != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin API key",
        )


@router.get("/providers/health", response_model=list[ProviderHealth])
async def list_provider_health() -> list[ProviderHealth]:
    """List health status of all configured providers."""
    # TODO: Wire up provider health checks
    return []


@router.get("/config")
async def get_config() -> dict:
    """Get current gateway configuration (sensitive values redacted)."""
    return {
        "gateway_env": settings.gateway_env,
        "enable_semantic_cache": settings.enable_semantic_cache,
        "enable_rate_limiting": settings.enable_rate_limiting,
        "enable_circuit_breaker": settings.enable_circuit_breaker,
        "enable_cost_tracking": settings.enable_cost_tracking,
        "enable_shadow_mode": settings.enable_shadow_mode,
    }
