"""Chat completion endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.responses import StreamingResponse

from app.core.models import ChatCompletionRequest, ChatCompletionResponse, ModelsResponse
from app.dependencies import verify_api_key
from app.providers.registry import get_registry
from app.router.engine import SmartRouter

router = APIRouter()


def get_router() -> SmartRouter:
    return SmartRouter(get_registry())


@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    request: Request,
    body: ChatCompletionRequest,
    api_key: str = Depends(verify_api_key),  # noqa: ARG001
    router: SmartRouter = Depends(get_router),
) -> ChatCompletionResponse:
    """Create a chat completion — OpenAI-compatible endpoint."""
    if body.stream:
        raise HTTPException(status_code=400, detail="Use the streaming endpoint for stream=True")
    return await router.route_chat_completion(body)


@router.post("/chat/completions/stream")
async def create_chat_completion_stream(
    request: Request,
    body: ChatCompletionRequest,
    api_key: str = Depends(verify_api_key),  # noqa: ARG001
    router: SmartRouter = Depends(get_router),
) -> StreamingResponse:
    """Stream a chat completion — SSE."""

    async def event_generator():
        async for chunk in router.route_chat_completion_stream(body):
            yield f"data: {chunk.model_dump_json()}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )


@router.get("/models", response_model=ModelsResponse)
async def list_models(
    api_key: str = Depends(verify_api_key),  # noqa: ARG001
) -> ModelsResponse:
    """List all available models across all providers."""
    registry = get_registry()
    models = registry.list_all_models()
    return ModelsResponse(data=models)
