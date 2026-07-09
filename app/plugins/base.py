"""Base plugin interface for custom gateway middleware."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from starlette.requests import Request
    from starlette.responses import Response


class GatewayPlugin(ABC):
    """Abstract base class for user-provided gateway plugins."""

    name: str = ""
    order: int = 0

    @abstractmethod
    async def process_request(self, request: Request) -> Request:
        """Inspect or mutate an incoming request."""
        ...

    @abstractmethod
    async def process_response(self, request: Request, response: Response) -> Response:
        """Inspect or mutate an outgoing response."""
        ...
