"""In-memory chat session store with async-compatible API.

This is intentionally lightweight for Day 29. In production it would be backed
by PostgreSQL via the existing DB layer.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import ClassVar


@dataclass
class ChatMessage:
    role: str
    content: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ChatSession:
    session_id: str
    user_id: str | None
    model: str
    messages: list[ChatMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class ChatSessionStore:
    """Async-compatible in-memory session store."""

    _instance: ClassVar[ChatSessionStore | None] = None

    def __new__(cls) -> ChatSessionStore:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._sessions: dict[str, ChatSession] = {}
        return cls._instance

    async def create(self, model: str, user_id: str | None = None) -> ChatSession:
        session_id = str(uuid.uuid4())
        session = ChatSession(session_id=session_id, user_id=user_id, model=model)
        self._sessions[session_id] = session
        return session

    async def get(self, session_id: str) -> ChatSession | None:
        return self._sessions.get(session_id)

    async def add_message(self, session_id: str, role: str, content: str) -> ChatSession | None:
        session = self._sessions.get(session_id)
        if session is None:
            return None
        session.messages.append(ChatMessage(role=role, content=content))
        session.updated_at = datetime.now(UTC)
        return session

    async def list_sessions(self, user_id: str | None = None) -> list[ChatSession]:
        sessions = list(self._sessions.values())
        if user_id is not None:
            sessions = [s for s in sessions if s.user_id == user_id]
        return sorted(sessions, key=lambda s: s.updated_at, reverse=True)

    async def delete(self, session_id: str) -> bool:
        return self._sessions.pop(session_id, None) is not None
