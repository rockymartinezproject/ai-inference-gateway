"""Chat completion endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.responses import StreamingResponse

from app.core.errors import ModelNotFound
from app.core.models import ChatCompletionRequest, ChatCompletionResponse, ModelsResponse
from app.dependencies import verify_api_key
from app.providers.registry import get_registry

router = APIRouter()


@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    request: Request,
    body: ChatCompletionRequest,
    api_key: str = Depends(verify_api_key),  # noqa: ARG001
) -> ChatCompletionResponse:
    """Create a chat completion — OpenAI-compatible endpoint."""
    registry = get_registry()

    # Find provider for requested model
    provider = registry.find_by_model(body.model)
    if provider is None:
        raise ModelNotFound(body.model)

    return await provider.chat_completion(body)


@router.get("/models", response_model=ModelsResponse)
async def list_models(
    api_key: str = Depends(verify_api_key),  # noqa: ARG001
) -> ModelsResponse:
    """List all available models across all providers."""
    registry = get_registry()
    models = registry.list_all_models()
    return ModelsResponse(data=models)
