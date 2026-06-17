"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as api_v1_router
from app.config import settings
from app.core.errors import GatewayException, gateway_exception_handler, generic_exception_handler
from app.core.logging import configure_logging
from app.core.middleware import LoggingMiddleware, RequestIDMiddleware, TimingMiddleware
from app.providers.factory import build_registry
from app.providers.registry import set_registry


def create_app() -> FastAPI:
    """Application factory."""
    configure_logging(settings.gateway_env)

    @asynccontextmanager
    async def lifespan(app: FastAPI):  # noqa: ARG001
        """Application lifespan — startup and shutdown."""
        registry = build_registry()
        set_registry(registry)
        # TODO: Initialize Redis, DB pools
        yield
        # TODO: Clean up connections
        for provider in registry.all():
            if hasattr(provider, "close"):
                await provider.close()

    app = FastAPI(
        title="AI Inference Gateway",
        description="Unified API gateway for multi-provider LLM inference",
        version="0.1.0",
        docs_url="/docs" if settings.gateway_env == "development" else None,
        redoc_url="/redoc" if settings.gateway_env == "development" else None,
        lifespan=lifespan,
    )

    # Middleware — order matters: outermost first
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(TimingMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    app.add_exception_handler(GatewayException, gateway_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # Routes
    app.include_router(api_v1_router)

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"message": "AI Inference Gateway", "version": "0.1.0"}

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.gateway_host,
        port=settings.gateway_port,
        workers=settings.gateway_workers,
        reload=settings.gateway_env == "development",
    )
