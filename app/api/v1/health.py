"""Health check endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel

from app.dependencies import optional_api_key

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str = "0.1.0"
    environment: str = "development"


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check(
    request: Request,
    api_key: str | None = Depends(optional_api_key),  # noqa: ARG001
) -> HealthResponse:
    """Basic liveness probe."""
    return HealthResponse(status="ok")


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check(
    request: Request,
    api_key: str | None = Depends(optional_api_key),  # noqa: ARG001
) -> dict[str, str]:
    """Readiness probe — checks dependencies."""
    # TODO: Check Redis, DB connectivity
    return {"status": "ready"}
