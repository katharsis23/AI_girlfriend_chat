"""Integration tests for the async SQLite provider (real file, tmp_path)."""

from uuid import uuid4

import pytest

from src.ai_girlfriend.database.sqlite_provider import SQLiteProvider
from src.ai_girlfriend.exc import StorageError
from src.ai_girlfriend.models.llm import Message, Role

pytestmark = pytest.mark.integration


@pytest.fixture
async def provider(tmp_path):
    db = SQLiteProvider(db_path=tmp_path / "test.db")
    await db.init()
    yield db
    await db.close()


async def test_exchange_roundtrip(provider):
    chat_id = await provider.create_chat()
    await provider.save_exchange(
        Message(conversation_id=chat_id, role=Role.USER, content="Hello"),
        Message(conversation_id=chat_id, role=Role.ASSISTANT, content="Hi"),
    )

    messages = await provider.get_recent_messages(chat_id, limit=10)
    assert [m.content for m in messages] == ["Hello", "Hi"]
    assert [m.role for m in messages] == [Role.USER, Role.ASSISTANT]


async def test_recent_messages_are_ordered_and_limited(provider):
    chat_id = await provider.create_chat()
    for i in range(5):
        await provider.save_message(
            Message(conversation_id=chat_id, role=Role.USER, content=f"m{i}")
        )

    recent = await provider.get_recent_messages(chat_id, limit=2)
    assert [m.content for m in recent] == ["m3", "m4"]


async def test_history_is_isolated_per_chat(provider):
    a = await provider.create_chat()
    b = await provider.create_chat()
    await provider.save_message(
        Message(conversation_id=a, role=Role.USER, content="in-a")
    )

    assert await provider.get_recent_messages(b, limit=10) == []
    assert [m.content for m in await provider.get_recent_messages(a, limit=10)] == [
        "in-a"
    ]


async def test_operations_before_init_raise_storage_error(tmp_path):
    db = SQLiteProvider(db_path=tmp_path / "uninit.db")
    with pytest.raises(StorageError):
        await db.get_recent_messages(uuid4(), limit=1)


async def test_save_exchange_is_atomic_on_conflict(provider):
    """A duplicate primary key must roll back the whole exchange."""
    chat_id = await provider.create_chat()
    user = Message(conversation_id=chat_id, role=Role.USER, content="u")

    # First exchange succeeds.
    await provider.save_exchange(
        user, Message(conversation_id=chat_id, role=Role.ASSISTANT, content="a")
    )

    # Re-using the same user id triggers a PK conflict on the first insert.
    duplicate = Message(
        id=user.id, conversation_id=chat_id, role=Role.USER, content="u-again"
    )
    with pytest.raises(StorageError):
        await provider.save_exchange(
            duplicate,
            Message(conversation_id=chat_id, role=Role.ASSISTANT, content="a2"),
        )

    # Nothing from the failed exchange was persisted.
    messages = await provider.get_recent_messages(chat_id, limit=10)
    assert [m.content for m in messages] == ["u", "a"]
