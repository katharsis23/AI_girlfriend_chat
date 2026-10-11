"""Contract tests: every ``IDatabaseStorage`` implementation must pass these.

The same suite runs against the in-memory fake and the SQLite provider.
"""

import pytest

from src.ai_girlfriend.database.sqlite_provider import SQLiteProvider
from src.ai_girlfriend.models.llm import Message, Role
from src.ai_girlfriend.testing.in_memory_db import InMemoryDatabaseProvider

pytestmark = pytest.mark.contract


def make_message(chat_id, role: Role, content: str) -> Message:
    return Message(conversation_id=chat_id, role=role, content=content)


async def _contract_roundtrip(provider):
    chat_id = await provider.create_chat()

    user = make_message(chat_id, Role.USER, "Hello")
    bot = make_message(chat_id, Role.ASSISTANT, "Hi there")
    await provider.save_exchange(user, bot)

    messages = await provider.get_recent_messages(chat_id, limit=10)
    assert [m.role for m in messages] == [Role.USER, Role.ASSISTANT]
    assert [m.content for m in messages] == ["Hello", "Hi there"]
    assert all(m.conversation_id == chat_id for m in messages)


async def _contract_limit(provider):
    chat_id = await provider.create_chat()
    for i in range(5):
        await provider.save_message(make_message(chat_id, Role.USER, f"m{i}"))

    recent = await provider.get_recent_messages(chat_id, limit=2)
    assert [m.content for m in recent] == ["m3", "m4"]


async def _contract_create_chat_is_unique(provider):
    a = await provider.create_chat()
    b = await provider.create_chat()
    assert a != b


async def _contract_empty_history(provider):
    chat_id = await provider.create_chat()
    assert await provider.get_recent_messages(chat_id, limit=10) == []


CONTRACTS = [
    _contract_roundtrip,
    _contract_limit,
    _contract_create_chat_is_unique,
    _contract_empty_history,
]


@pytest.mark.parametrize(
    "provider_factory",
    [
        pytest.param(lambda tmp: InMemoryDatabaseProvider(), id="in_memory"),
        pytest.param(
            lambda tmp: SQLiteProvider(db_path=tmp / "contract.db"), id="sqlite"
        ),
    ],
)
@pytest.mark.parametrize("contract", CONTRACTS)
async def test_provider_contract(provider_factory, contract, tmp_path):
    provider = provider_factory(tmp_path)
    await provider.init()
    try:
        await contract(provider)
    finally:
        await provider.close()
