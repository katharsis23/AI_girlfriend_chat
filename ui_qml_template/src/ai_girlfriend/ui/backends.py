"""QML <-> core bridge (spec §4). QML renders, Python holds state, the core does the work."""

from __future__ import annotations

import asyncio
import inspect
import threading
from concurrent.futures import Future
from pathlib import Path
from typing import Any

from PySide6.QtCore import Property, QObject, QThread, QUrl, Signal, Slot

from .themes import THEMES, ThemeController


class AsyncWorker(QThread):
    """asyncio loop living in its own QThread: the GUI thread never blocks (spec §2)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._loop: asyncio.AbstractEventLoop | None = None
        self._ready = threading.Event()

    def run(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._ready.set()
        self._loop.run_forever()
        self._loop.close()

    def start_and_wait(self) -> None:
        self.start()
        self._ready.wait()

    def submit(self, coro) -> Future:
        assert self._loop is not None, "AsyncWorker not started"
        return asyncio.run_coroutine_threadsafe(coro, self._loop)

    def stop(self) -> None:
        if self._loop is not None:
            self._loop.call_soon_threadsafe(self._loop.stop)
        self.wait(2000)


def _expression_url(character: Any, expression: str) -> str:
    """Per-character expression asset (photo_emoji_map) -> file URL, or '' to use the emoji fallback."""
    try:
        path = (getattr(character, "photo_emoji_map", None) or {}).get(expression)
        if path and Path(path).is_file():
            return QUrl.fromLocalFile(str(Path(path).resolve())).toString()
    except Exception:
        pass
    return ""


class ChatBackend(QObject):
    busyChanged = Signal(bool)
    messageAppended = Signal(str, str)  # role, text
    expressionChanged = Signal(str)
    errorRaised = Signal(str)
    characterChanged = Signal()
    _replyReady = Signal(object)

    def __init__(self, worker: AsyncWorker, pipeline: Any, character: Any, parent=None):
        super().__init__(parent)
        self._worker = worker
        self._pipeline = pipeline
        self._character = character
        self._chat_id: Any = None
        self._busy = False
        self._replyReady.connect(self._on_reply)

    # --- properties -----------------------------------------------------
    @Property(bool, notify=busyChanged)
    def busy(self):
        return self._busy

    @Property(str, notify=characterChanged)
    def characterName(self):
        return getattr(self._character, "name", "")

    @Property(str, notify=characterChanged)
    def greeting(self):
        return getattr(self._character, "greeting", "") or ""

    @Property(str, notify=characterChanged)
    def initialExpression(self):
        return getattr(self._character, "initial_expression", "neutral") or "neutral"

    # --- slots ----------------------------------------------------------
    @Slot(str)
    def sendMessage(self, text: str) -> None:
        text = text.strip()
        if not text or self._busy:
            return
        self.messageAppended.emit("user", text)
        self._set_busy(True)

        async def call():
            result = self._pipeline.chat(text, chat_id=self._chat_id)
            return await result if inspect.isawaitable(result) else result

        self._worker.submit(call()).add_done_callback(self._replyReady.emit)

    @Slot()
    def resetChat(self) -> None:
        self._chat_id = None
        self.expressionChanged.emit(self.initialExpression)

    @Slot(str, result=str)
    def expressionUrl(self, expression: str) -> str:
        return _expression_url(self._character, expression)

    # --- internals ------------------------------------------------------
    def apply_character(self, pipeline: Any, character: Any) -> None:
        """Called by SettingsBackend after the pipeline was rebuilt (spec §6.2)."""
        self._pipeline, self._character = pipeline, character
        self._chat_id = None
        self.characterChanged.emit()
        self.expressionChanged.emit(self.initialExpression)

    def _set_busy(self, value: bool) -> None:
        if self._busy != value:
            self._busy = value
            self.busyChanged.emit(value)

    @Slot(object)
    def _on_reply(self, fut: Future) -> None:
        try:
            reply = fut.result()
        except Exception as exc:
            self._set_busy(False)
            self.errorRaised.emit(str(exc) or exc.__class__.__name__)
            return
        text = (
            getattr(reply, "text", None)
            or getattr(reply, "content", None)
            or str(reply)
        )
        self._chat_id = getattr(reply, "chat_id", self._chat_id)
        self.messageAppended.emit("assistant", text)
        expression = getattr(reply, "expression", None)
        if expression:
            self.expressionChanged.emit(expression)
        self._set_busy(False)


class SettingsBackend(QObject):
    currentThemeChanged = Signal()
    currentCharacterChanged = Signal()
    themeApplied = Signal(str)
    characterChanged = Signal(str)
    busyChanged = Signal(bool)
    _built = Signal(object, str)

    def __init__(
        self,
        worker,
        root,
        chat: ChatBackend,
        theme: ThemeController,
        character: Any,
        parent=None,
    ):
        super().__init__(parent)
        self._worker, self._root, self._chat, self._theme = worker, root, chat, theme
        self._characters = list(root.config.characters)
        self._current = character.character_id
        self._busy = False
        self._built.connect(self._on_built)

    @Property("QStringList", constant=True)
    def themes(self):
        return list(THEMES)

    @Property(str, notify=currentThemeChanged)
    def currentTheme(self):
        return self._theme.themeId

    @Property("QStringList", constant=True)
    def characters(self):
        return [c.character_id for c in self._characters]

    @Property(str, notify=currentCharacterChanged)
    def currentCharacter(self):
        return self._current

    @Property(bool, notify=busyChanged)
    def busy(self):
        return self._busy

    @Slot(str)
    def selectTheme(self, theme_id: str) -> None:
        if theme_id not in THEMES:
            return
        self._theme.setTheme(theme_id)
        self.currentThemeChanged.emit()
        self.themeApplied.emit(theme_id)

    @Slot(str)
    def selectCharacter(self, character_id: str) -> None:
        if self._busy or character_id == self._current:
            return
        info = next(
            (c for c in self._characters if c.character_id == character_id), None
        )
        if info is None:
            return
        self._set_busy(True)

        async def build():
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                None, lambda: self._root.build_pipeline(character=info)
            )

        def done(fut: Future) -> None:
            self._built.emit(fut, character_id)

        self._worker.submit(build()).add_done_callback(done)

    # --- view helpers (display data for the pickers) --------------------
    @Slot(str, result="QVariantMap")
    def themeInfo(self, theme_id: str):
        t = THEMES[theme_id]
        c = t["colors"]
        return {
            "name": t["name"],
            "dark": t["dark"],
            "primary": c["primary"],
            "secondary": c["secondary"],
            "background": c["background"],
        }

    @Slot(str, result="QVariantMap")
    def characterInfo(self, character_id: str):
        c = next(c for c in self._characters if c.character_id == character_id)
        expr = getattr(c, "initial_expression", "neutral")
        return {
            "name": c.name,
            "personality": getattr(c, "personality", "") or "",
            "expression": expr,
            "thumb": _expression_url(c, expr),
        }

    # --- internals ------------------------------------------------------
    def _set_busy(self, value: bool) -> None:
        if self._busy != value:
            self._busy = value
            self.busyChanged.emit(value)

    @Slot(object, str)
    def _on_built(self, fut: Future, character_id: str) -> None:
        try:
            pipeline = fut.result()
        except Exception as exc:
            self._set_busy(False)
            self._chat.errorRaised.emit(str(exc) or exc.__class__.__name__)
            return
        info = next(c for c in self._characters if c.character_id == character_id)
        self._current = character_id
        self._chat.apply_character(pipeline, info)  # fresh chat_id, greeting, portrait
        self.currentCharacterChanged.emit()
        self.characterChanged.emit(character_id)
        self._set_busy(False)
