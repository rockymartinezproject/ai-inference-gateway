"""Shared Pydantic models for the AI Inference Gateway."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class Role(str, Enum):
    """Chat message roles."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    """A single chat message."""

    role: Role
    content: str


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible chat completion request."""

    model: str
    messages: list[ChatMessage]
    temperature: float | None = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, ge=1)
    top_p: float | None = Field(default=1.0, ge=0.0, le=1.0)
    stream: bool = False
    user: str | None = None

    # Gateway-specific routing hints
    prefer_low_cost: bool = False
    prefer_low_latency: bool = False
    fallback_models: list[str] | None = None


class Usage(BaseModel):
    """Token usage statistics."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class Choice(BaseModel):
    """A completion choice."""

    index: int = 0
    message: ChatMessage | None = None
    delta: ChatMessage | None = None
    finish_reason: str | None = None


class ChatCompletionResponse(BaseModel):
    """OpenAI-compatible chat completion response."""

    id: str
    object: Literal["chat.completion"] = "chat.completion"
    created: int
    model: str
    choices: list[Choice]
    usage: Usage


class ChatCompletionStreamChunk(BaseModel):
    """SSE stream chunk for chat completions."""

    id: str
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    created: int
    model: str
    choices: list[Choice]


class EmbeddingRequest(BaseModel):
    """Embedding request."""

    input: str | list[str]
    model: str
    user: str | None = None


class EmbeddingData(BaseModel):
    """Single embedding result."""

    object: Literal["embedding"] = "embedding"
    embedding: list[float]
    index: int


class EmbeddingResponse(BaseModel):
    """Embedding response."""

    object: Literal["list"] = "list"
    data: list[EmbeddingData]
    model: str
    usage: Usage


class ModelInfo(BaseModel):
    """Provider model metadata."""

    id: str
    object: Literal["model"] = "model"
    owned_by: str
    context_length: int | None = None
    cost_per_1k_input: float | None = None
    cost_per_1k_output: float | None = None
    capabilities: list[str] = Field(default_factory=list)


class ModelsResponse(BaseModel):
    """List of available models."""

    object: Literal["list"] = "list"
    data: list[ModelInfo]


class ProviderStatus(str, Enum):
    """Provider health status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    DISABLED = "disabled"


class ProviderHealth(BaseModel):
    """Provider health check result."""

    provider: str
    status: ProviderStatus
    latency_ms: float | None = None
    last_checked: str | None = None
    error: str | None = None


class GatewayError(BaseModel):
    """Standard error response."""

    error: dict[str, Any]
