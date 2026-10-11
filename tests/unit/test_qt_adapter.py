"""Unit tests for the Qt adapter.

These tests skip automatically when PySide6 is not installed. They run headless
with the ``offscreen`` Qt platform plugin.
"""

import json
import os
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from src.ai_girlfriend.character.expression_manager import ExpressionManager
from src.ai_girlfriend.database.conversation_window import (
    ConversationWindowProvider,
)
from src.ai_girlfriend.database.database_controller import DatabaseController
from src.ai_girlfriend.database.memory_manager import MemoryManager
from src.ai_girlfriend.gf_pipeline import GfPipeline
from src.ai_girlfriend.llm.llm_provider import AIController
from src.ai_girlfriend.models.character import CharacterInfo
from src.ai_girlfriend.testing.fake_llm import FakeLLMProvider
from src.ai_girlfriend.testing.in_memory_db import InMemoryDatabaseProvider
from src.ai_girlfriend.ui_builder.chat_window import ChatWindow

pytestmark = pytest.mark.unit


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def make_character(tmp_path: Path) -> CharacterInfo:
    asset = tmp_path / "neutral.png"
    asset.write_bytes(b"not-a-real-png")
    return CharacterInfo(
        name="Aria",
        personality="You are Aria.",
        photo_emoji_map={"neutral": "neutral.png"},
        initial_expression="neutral",
        greeting_message="Hi there!",
    )


async def make_pipeline(provider: FakeLLMProvider, tmp_path: Path) -> GfPipeline:
    character = make_character(tmp_path)
    db = DatabaseController(InMemoryDatabaseProvider())
    await db.init()
    context = ConversationWindowProvider(database=db, window=5)
    return GfPipeline(
        gf_config=character,
        ai_controller=AIController(provider),
        memory_manager=MemoryManager(database=db, context_provider=context),
        expression_manager=ExpressionManager(character, base_dir=tmp_path),
    )


class _FakeWorker(QObject):
    """A synchronous stand-in for ``AsyncWorker`` used in tests."""

    finished = Signal(object)
    failed = Signal(object)

    def submit(self, coro):
        import asyncio
        import threading

        box: dict[str, object] = {}

        def _run() -> None:
            loop = asyncio.new_event_loop()
            try:
                box["result"] = loop.run_until_complete(coro)
            except Exception as exc:
                box["error"] = exc
            finally:
                loop.close()

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            # No loop running in this thread: run inline.
            _run()
        else:
            # pytest-asyncio runs an event loop in the main thread; drive the
            # coroutine in a helper thread so the two loops don't clash
            # (mirroring the real ``AsyncWorker``'s dedicated thread).
            thread = threading.Thread(target=_run)
            thread.start()
            thread.join()

        if "error" in box:
            self.failed.emit(box["error"])
        else:
            self.finished.emit(box.get("result"))


async def test_window_shows_greeting_and_portrait(qapp, tmp_path):
    pipeline = await make_pipeline(FakeLLMProvider(), tmp_path)
    window = ChatWindow(pipeline, _FakeWorker())

    assert "Hi there!" in window.transcript.toPlainText()
    assert window.input.placeholderText()


async def test_send_appends_user_message(qapp, tmp_path):
    provider = FakeLLMProvider(
        response=json.dumps({"text": "Hello!", "expression": "neutral"})
    )
    pipeline = await make_pipeline(provider, tmp_path)
    window = ChatWindow(pipeline, _FakeWorker())

    window.input.setText("hey")
    window.send()

    assert "You: hey" in window.transcript.toPlainText()


async def test_send_renders_assistant_response(qapp, tmp_path):
    provider = FakeLLMProvider(
        response=json.dumps({"text": "Hello!", "expression": "neutral"})
    )
    pipeline = await make_pipeline(provider, tmp_path)
    window = ChatWindow(pipeline, _FakeWorker())

    window.input.setText("hey")
    window.send()

    text = window.transcript.toPlainText()
    assert "You: hey" in text
    assert "Hello!" in text
    assert window.send_button.isEnabled()


async def test_stream_error_shows_message(qapp, tmp_path):
    from src.ai_girlfriend.exc import ProviderError

    provider = FakeLLMProvider(error=ProviderError("nope"))
    pipeline = await make_pipeline(provider, tmp_path)
    window = ChatWindow(pipeline, _FakeWorker())

    window.input.setText("hey")
    window.send()

    assert "Error:" in window.transcript.toPlainText()
    assert window.send_button.isEnabled()


async def test_missing_asset_does_not_crash(qapp, tmp_path):
    character = CharacterInfo(
        name="Aria",
        personality="x",
        photo_emoji_map={"neutral": "missing.png"},
        initial_expression="neutral",
    )
    db = DatabaseController(InMemoryDatabaseProvider())
    await db.init()
    context = ConversationWindowProvider(database=db, window=5)
    pipeline = GfPipeline(
        gf_config=character,
        ai_controller=AIController(FakeLLMProvider()),
        memory_manager=MemoryManager(database=db, context_provider=context),
        expression_manager=ExpressionManager(character, base_dir=tmp_path),
    )
    window = ChatWindow(pipeline, _FakeWorker())

    assert "neutral" in window.portrait.text()
