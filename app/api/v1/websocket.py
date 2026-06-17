"""WebSocket streaming endpoint."""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.models import ChatCompletionRequest, ChatMessage
from app.providers.registry import get_registry
from app.router.engine import SmartRouter

router = APIRouter()


def get_router() -> SmartRouter:
    return SmartRouter(get_registry())


@router.websocket("/ws/chat")
async def websocket_chat(
    websocket: WebSocket,
) -> None:
    """WebSocket endpoint for bidirectional chat streaming."""
    await websocket.accept()
    router = get_router()

    try:
        while True:
            data = await websocket.receive_json()
            messages = [ChatMessage(**m) for m in data.get("messages", [])]
            request = ChatCompletionRequest(
                model=data.get("model", "gpt-4o"),
                messages=messages,
                temperature=data.get("temperature"),
                max_tokens=data.get("max_tokens"),
                stream=True,
            )

            try:
                async for chunk in router.route_chat_completion_stream(request):
                    await websocket.send_json(chunk.model_dump())
                await websocket.send_json({"done": True})
            except Exception as exc:
                await websocket.send_json({"error": str(exc)})
    except WebSocketDisconnect:
        pass
