"""FastAPI dependencies."""

from __future__ import annotations

from fastapi import Header, HTTPException, status

from app.config import settings


async def verify_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> str:
    """Verify user API key from header."""
    # TODO: Implement proper API key validation against database
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
        )
    return x_api_key
