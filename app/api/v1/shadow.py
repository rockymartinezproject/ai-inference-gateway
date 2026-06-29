"""Shadow mode and request replay endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import verify_admin_key
from app.providers.registry import get_registry
from app.shadow.replay import ShadowMode

router = APIRouter()


def get_shadow_mode() -> ShadowMode:
    return ShadowMode(get_registry())


@router.post("/shadow/enable")
async def enable_shadow_mode(
    providers: list[str],
    admin_key: str = Depends(verify_admin_key),  # noqa: ARG001
    shadow: ShadowMode = Depends(get_shadow_mode),
) -> dict:
    """Enable shadow mode for specified providers."""
    shadow.enable(providers)
    return {"status": "enabled", "targets": providers}


@router.post("/shadow/disable")
async def disable_shadow_mode(
    admin_key: str = Depends(verify_admin_key),  # noqa: ARG001
    shadow: ShadowMode = Depends(get_shadow_mode),
) -> dict:
    """Disable shadow mode."""
    shadow.disable()
    return {"status": "disabled"}


@router.get("/shadow/report")
async def get_shadow_report(
    admin_key: str = Depends(verify_admin_key),  # noqa: ARG001
    shadow: ShadowMode = Depends(get_shadow_mode),
) -> dict:
    """Get shadow traffic comparison report."""
    return shadow.get_comparison_report()
