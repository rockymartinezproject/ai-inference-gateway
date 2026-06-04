"""API v1 router aggregator."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import admin, completions, health

router = APIRouter(prefix="/v1")

router.include_router(health.router, tags=["health"])
router.include_router(completions.router, tags=["completions"])
router.include_router(admin.router, prefix="/admin", tags=["admin"])
