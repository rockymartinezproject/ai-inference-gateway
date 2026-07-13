"""Exception handlers and custom exceptions."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.models import GatewayError


class GatewayException(Exception):
    """Base gateway exception."""

    def __init__(self, message: str, status_code: int = 500, code: str = "internal_error") -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


class ProviderError(GatewayException):
    """Provider-specific error."""

    def __init__(self, message: str, provider: str | None = None) -> None:
        super().__init__(message, status_code=502, code="provider_error")
        self.provider = provider


class RateLimitExceeded(GatewayException):
    """Rate limit exceeded."""

    def __init__(self, message: str = "Rate limit exceeded") -> None:
        super().__init__(message, status_code=429, code="rate_limit_exceeded")


class ModelNotFound(GatewayException):
    """Requested model not found."""

    def __init__(self, model: str) -> None:
        super().__init__(f"Model '{model}' not found", status_code=404, code="model_not_found")


class AuthenticationError(GatewayException):
    """Authentication failed."""

    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message, status_code=401, code="authentication_error")


async def gateway_exception_handler(request: Request, exc: GatewayException) -> JSONResponse:
    """Handle custom gateway exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=GatewayError(
            error={
                "message": exc.message,
                "type": exc.code,
                "code": exc.status_code,
            }
        ).model_dump(),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    return JSONResponse(
        status_code=500,
        content=GatewayError(
            error={
                "message": "An unexpected error occurred",
                "type": "internal_error",
                "code": 500,
            }
        ).model_dump(),
    )
