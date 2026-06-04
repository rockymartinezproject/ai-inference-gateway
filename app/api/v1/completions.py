"""Chat completion endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.responses import StreamingResponse

from app.core.errors import GatewayException
from app.core.models import ChatCompletionRequest, ChatCompletionResponse

router = APIRouter()


@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    request: Request,
    body: ChatCompletionRequest,
) -> ChatCompletionResponse:
    """Create a chat completion — OpenAI-compatible endpoint."""
    # TODO: Wire up provider router
    raise HTTPException(status_code=501, detail="Not yet implemented")


@router.post("/chat/completions", response_model=None)
async def create_chat_completion_stream(
    request: Request,
    body: ChatCompletionRequest,
) -> StreamingResponse:
    """Stream a chat completion — SSE."""
    # TODO: Wire up streaming proxy
    raise HTTPException(status_code=501, detail="Not yet implemented")
