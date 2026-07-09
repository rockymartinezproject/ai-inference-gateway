"""Tests for chat session persistence."""

from __future__ import annotations

import pytest

from app.chat.sessions import ChatSessionStore


@pytest.fixture(autouse=True)
def fresh_store():
    # Reset the singleton between tests
    ChatSessionStore._instance = None
    ChatSessionStore._sessions = {}
    yield


@pytest.mark.anyio
async def test_create_session() -> None:
    store = ChatSessionStore()
    session = await store.create(model="gpt-4o", user_id="user-1")
    assert session.session_id
    assert session.model == "gpt-4o"
    assert session.user_id == "user-1"
    assert session.messages == []


@pytest.mark.anyio
async def test_get_session() -> None:
    store = ChatSessionStore()
    created = await store.create(model="gpt-4o")
    fetched = await store.get(created.session_id)
    assert fetched is not None
    assert fetched.session_id == created.session_id


@pytest.mark.anyio
async def test_add_message() -> None:
    store = ChatSessionStore()
    session = await store.create(model="gpt-4o")
    updated = await store.add_message(session.session_id, "user", "Hello")
    assert updated is not None
    assert len(updated.messages) == 1
    assert updated.messages[0].role == "user"
    assert updated.messages[0].content == "Hello"


@pytest.mark.anyio
async def test_list_sessions_by_user() -> None:
    store = ChatSessionStore()
    s1 = await store.create(model="gpt-4o", user_id="user-1")
    await store.create(model="claude-3", user_id="user-2")
    sessions = await store.list_sessions(user_id="user-1")
    assert len(sessions) == 1
    assert sessions[0].session_id == s1.session_id


@pytest.mark.anyio
async def test_delete_session() -> None:
    store = ChatSessionStore()
    session = await store.create(model="gpt-4o")
    deleted = await store.delete(session.session_id)
    assert deleted is True
    assert await store.get(session.session_id) is None
