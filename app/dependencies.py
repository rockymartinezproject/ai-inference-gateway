"""FastAPI dependencies."""

from __future__ import annotations

from fastapi import Header, HTTPException, Request, status

from app.config import settings


async def verify_api_key(
    request: Request,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> str:
    """Verify user API key from header and attach metadata to request state."""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Provide it via the X-API-Key header.",
        )

    # TODO: Validate against database and load user profile
    # For now we accept any non-empty key and derive a user id from it
    user_id = f"user_{x_api_key[:8]}"
    request.state.user_id = user_id
    request.state.api_key = x_api_key
    return x_api_key


async def optional_api_key(
    request: Request,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> str | None:
    """Optional API key — used for public health endpoints that still want to track callers."""
    if x_api_key:
        request.state.user_id = f"user_{x_api_key[:8]}"
        request.state.api_key = x_api_key
    return x_api_key


async def verify_admin_key(
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
) -> str:
    """Verify admin API key for management endpoints."""
    if not settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Admin API key not configured",
        )
    if not x_admin_key or x_admin_key != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin API key",
        )
    return x_admin_key
