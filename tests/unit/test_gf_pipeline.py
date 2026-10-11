"""Unit tests for ``GfPipeline`` using fakes (no network, disk, or GUI)."""

import json
from uuid import uuid4

import pytest

from src.ai_girlfriend.character.expression_manager import ExpressionManager
from src.ai_girlfriend.database.conversation_window import ConversationWindowProvider
from src.ai_girlfriend.database.database_controller import DatabaseController
from src.ai_girlfriend.database.memory_manager import MemoryManager
from src.ai_girlfriend.exc import ProviderError
from src.ai_girlfriend.gf_pipeline import GfPipeline
from src.ai_girlfriend.llm.llm_provider import AIController
from src.ai_girlfriend.models.character import CharacterInfo
from src.ai_girlfriend.models.events import Done, TextDelta
from src.ai_girlfriend.testing.fake_llm import FakeLLMProvider
from src.ai_girlfriend.testing.in_memory_db import InMemoryDatabaseProvider

pytestmark = pytest.mark.unit


def make_character(expressions: dict[str, str] | None = None) -> CharacterInfo:
    return CharacterInfo(
        name="Aria",
        personality="You are Aria.",
        photo_emoji_map=expressions or {"neutral": "neutral.png", "happy": "happy.png"},
        initial_expression="neutral",
    )


async def build_pipeline(
    provider: FakeLLMProvider, character: CharacterInfo | None = None
):
    character = character or make_character()
    db = DatabaseController(InMemoryDatabaseProvider())
    await db.init()
    context = ConversationWindowProvider(database=db, window=10)
    memory = MemoryManager(database=db, context_provider=context)
    return GfPipeline(
        gf_config=character,
        ai_controller=AIController(provider),
        memory_manager=memory,
        expression_manager=ExpressionManager(character),
    )


async def test_chat_returns_text_and_valid_expression():
    provider = FakeLLMProvider(
        response=json.dumps({"text": "Hi!", "expression": "happy"})
    )
    pipeline = await build_pipeline(provider)

    response = await pipeline.chat("hello")

    assert response.text == "Hi!"
    assert response.expression == "happy"


async def test_chat_falls_back_to_initial_expression_on_bad_id():
    provider = FakeLLMProvider(
        response=json.dumps({"text": "Hi!", "expression": "../../etc/passwd"})
    )
    pipeline = await build_pipeline(provider)

    response = await pipeline.chat("hello")

    assert response.expression == "neutral"


async def test_chat_uses_raw_text_when_output_is_not_json():
    provider = FakeLLMProvider(response="Just plain text")
    pipeline = await build_pipeline(provider)

    response = await pipeline.chat("hello")

    assert response.text == "Just plain text"
    assert response.expression == "neutral"


async def test_chat_persists_exchange_and_reuses_history():
    provider = FakeLLMProvider(
        responder=lambda req: json.dumps(
            {"text": f"re:{req.messages[-1].content}", "expression": "neutral"}
        )
    )
    pipeline = await build_pipeline(provider)
    chat_id = uuid4()

    first = await pipeline.chat("first", chat_id=chat_id)
    second = await pipeline.chat("second", chat_id=chat_id)

    assert first.text == "re:first"
    assert second.text == "re:second"

    stored = await pipeline.memory_manager.database.get_recent_messages(
        chat_id, limit=10
    )
    assert [m.content for m in stored] == ["first", "re:first", "second", "re:second"]


async def test_chat_creates_chat_when_id_is_missing():
    """A message without a chat_id must create the chat row (FK-safe)."""
    provider = FakeLLMProvider(
        response=json.dumps({"text": "Hi!", "expression": "neutral"})
    )
    pipeline = await build_pipeline(provider)

    response = await pipeline.chat("hello")  # no chat_id

    assert response.chat_id is not None
    stored = await pipeline.memory_manager.database.get_recent_messages(
        response.chat_id, limit=10
    )
    assert [m.content for m in stored] == ["hello", "Hi!"]


async def test_stream_chat_creates_chat_when_id_is_missing():
    provider = FakeLLMProvider(chunks=["Hel", "lo"])
    pipeline = await build_pipeline(provider)

    events = [e async for e in pipeline.stream_chat("hi")]
    assert isinstance(events[-1], Done)


async def test_chat_does_not_save_on_generation_failure():
    provider = FakeLLMProvider(error=RuntimeError("boom"))
    pipeline = await build_pipeline(provider)
    chat_id = uuid4()

    with pytest.raises(ProviderError):
        await pipeline.chat("hello", chat_id=chat_id)

    stored = await pipeline.memory_manager.database.get_recent_messages(
        chat_id, limit=10
    )
    assert stored == []


async def test_stream_chat_saves_only_on_done():
    provider = FakeLLMProvider(chunks=["Hel", "lo"])
    pipeline = await build_pipeline(provider)
    chat_id = uuid4()

    events = [e async for e in pipeline.stream_chat("hi", chat_id=chat_id)]

    deltas = [e for e in events if isinstance(e, TextDelta)]
    assert [d.text for d in deltas] == ["Hel", "lo"]
    assert isinstance(events[-1], Done)

    stored = await pipeline.memory_manager.database.get_recent_messages(
        chat_id, limit=10
    )
    assert [m.content for m in stored] == ["hi", "Hello"]


async def test_stream_chat_cancellation_saves_nothing():
    provider = FakeLLMProvider(chunks=["a", "b", "c"])
    pipeline = await build_pipeline(provider)
    chat_id = uuid4()

    agen = pipeline.stream_chat("hi", chat_id=chat_id)
    await anext(agen)  # receive first delta only
    await agen.aclose()  # simulate "stop"

    stored = await pipeline.memory_manager.database.get_recent_messages(
        chat_id, limit=10
    )
    assert stored == []
