"""Unit tests for ``MemoryManager`` and ``ConversationWindowProvider``."""

from uuid import uuid4

import pytest

from src.ai_girlfriend.database.conversation_window import ConversationWindowProvider
from src.ai_girlfriend.database.database_controller import DatabaseController
from src.ai_girlfriend.database.memory_manager import MemoryManager
from src.ai_girlfriend.models.llm import Message, Role
from src.ai_girlfriend.testing.in_memory_db import InMemoryDatabaseProvider

pytestmark = pytest.mark.unit


async def _make_manager(window: int = 10):
    provider = InMemoryDatabaseProvider()
    controller = DatabaseController(provider)
    await controller.init()
    context = ConversationWindowProvider(database=controller, window=window)
    return MemoryManager(database=controller, context_provider=context), controller


async def test_build_context_returns_recent_history():
    manager, controller = await _make_manager()
    chat_id = await controller.create_chat()
    for i in range(3):
        await controller.save_message(
            Message(conversation_id=chat_id, role=Role.USER, content=f"m{i}")
        )

    query = Message(conversation_id=chat_id, role=Role.USER, content="m3")
    bundle = await manager.build_context(chat_id, query)

    assert [m.content for m in bundle.messages] == ["m0", "m1", "m2"]
    assert bundle.memories == []


async def test_window_limits_history():
    manager, controller = await _make_manager(window=2)
    chat_id = await controller.create_chat()
    for i in range(5):
        await controller.save_message(
            Message(conversation_id=chat_id, role=Role.USER, content=f"m{i}")
        )

    query = Message(conversation_id=chat_id, role=Role.USER, content="m5")
    bundle = await manager.build_context(chat_id, query)

    assert [m.content for m in bundle.messages] == ["m3", "m4"]


async def test_record_exchange_persists_both_messages():
    manager, controller = await _make_manager()
    chat_id = await controller.create_chat()

    user = Message(conversation_id=chat_id, role=Role.USER, content="hi")
    bot = Message(conversation_id=chat_id, role=Role.ASSISTANT, content="hello")
    await manager.record_exchange(user, bot)

    stored = await controller.get_recent_messages(chat_id, limit=10)
    assert [m.content for m in stored] == ["hi", "hello"]


async def test_record_exchange_failure_raises_and_saves_nothing():
    provider = InMemoryDatabaseProvider(fail_on_save=True)
    controller = DatabaseController(provider)
    await controller.init()
    context = ConversationWindowProvider(database=controller, window=10)
    manager = MemoryManager(database=controller, context_provider=context)

    chat_id = uuid4()
    user = Message(conversation_id=chat_id, role=Role.USER, content="hi")
    bot = Message(conversation_id=chat_id, role=Role.ASSISTANT, content="hello")

    with pytest.raises(RuntimeError):
        await manager.record_exchange(user, bot)

    assert await controller.get_recent_messages(chat_id, limit=10) == []
