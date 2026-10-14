"""QML <-> core bridge (spec §4). QML renders, Python holds state, the core does the work."""

from __future__ import annotations

import asyncio
import inspect
import threading
from concurrent.futures import Future
from pathlib import Path
from typing import Any

from PySide6.QtCore import Property, QObject, QThread, QUrl, Signal, Slot

from src.ai_girlfriend.ui.characters_store import CharacterStore
from src.ai_girlfriend.ui.themes import REQUIRED_TOKENS, THEMES, ThemeController


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


def _character_greeting(character: Any) -> str:
    """Greeting text, tolerating both ``greeting_message`` (core) and ``greeting``."""
    return (
        getattr(character, "greeting_message", None)
        or getattr(character, "greeting", None)
        or ""
    )


def _optional_float(value: Any) -> float | None:
    """Coerce a form value to ``float``; empty/invalid becomes ``None``."""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _optional_int(value: Any) -> int | None:
    """Coerce a form value to ``int``; empty/invalid becomes ``None``."""
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _is_image(path: Path) -> bool:
    from src.ai_girlfriend.ui.filesystem import IMAGE_SUFFIXES

    return path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES


def _url_for_path(path: Path) -> str:
    return QUrl.fromLocalFile(str(path.resolve())).toString()


def _format_timestamp(value: Any) -> str:
    """Human-friendly timestamp for the history list; '' when unavailable."""
    if value is None:
        return ""
    try:
        return value.strftime("%Y-%m-%d %H:%M")
    except (AttributeError, ValueError):
        return str(value)


def _expression_url(character: Any, expression: str, pipeline: Any = None) -> str:
    """Resolve an expression id to a file URL, or '' to use the emoji fallback.

    The core stores asset paths relative to the character directory, so we route
    through ``ExpressionManager.asset_path`` (which applies ``base_dir`` and the
    traversal guard) whenever the pipeline is available. Falling back to a bare
    ``photo_emoji_map`` lookup keeps the demo path working.

    Robust fallback (task 4): if the requested emotion has no usable image on
    disk (unknown id, missing file, hallucinated emotion), we walk a chain of
    candidates — the resolved id, then ``initial_expression``, then ``default``,
    then any mapped asset — and return the first that exists. Only when nothing
    is available do we return '' so the QML layer shows the emoji placeholder.
    """
    manager = getattr(pipeline, "expression_manager", None)
    raw_map = dict(getattr(character, "photo_emoji_map", None) or {})
    initial = getattr(character, "initial_expression", None)

    candidates: list[str] = []
    for candidate in (expression, initial, "default"):
        if candidate and candidate not in candidates:
            candidates.append(candidate)
    for candidate in raw_map:
        if candidate not in candidates:
            candidates.append(candidate)

    for candidate_id in candidates:
        try:
            if manager is not None:
                path = manager.asset_path(candidate_id)
            else:
                raw = raw_map.get(candidate_id)
                path = Path(raw).expanduser() if raw else None
            if path is not None and _is_image(Path(path)):
                return _url_for_path(Path(path))
        except Exception:
            continue
    return ""


class ChatBackend(QObject):
    busyChanged = Signal(bool)
    messageAppended = Signal(str, str)  # role, text
    expressionChanged = Signal(str)
    errorRaised = Signal(str)
    characterChanged = Signal()
    # History: emitted with a list of chat summaries, and with a loaded
    # transcript (list of {role, text} maps) when a previous chat is opened.
    chatsListed = Signal("QVariantList")
    chatLoaded = Signal(str, "QVariantList")
    _replyReady = Signal(object)
    _chatsReady = Signal(object)
    _messagesReady = Signal(object, str)

    def __init__(self, worker: AsyncWorker, pipeline: Any, character: Any, parent=None):
        super().__init__(parent)
        self._worker = worker
        self._pipeline = pipeline
        self._character = character
        self._chat_id: Any = None
        self._busy = False
        self._replyReady.connect(self._on_reply)
        self._chatsReady.connect(self._on_chats)
        self._messagesReady.connect(self._on_messages)

    # --- properties -----------------------------------------------------
    @Property(bool, notify=busyChanged)
    def busy(self):
        return self._busy

    @Property(str, notify=characterChanged)
    def characterName(self):
        return getattr(self._character, "name", "")

    @Property(str, notify=characterChanged)
    def greeting(self):
        return _character_greeting(self._character)

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
        return _expression_url(self._character, expression, self._pipeline)

    # --- history (read-only views into stored conversations) -------------
    @Property(str, notify=characterChanged)
    def currentChatId(self):
        return "" if self._chat_id is None else str(self._chat_id)

    @Slot(int)
    def listChats(self, limit: int = 50) -> None:
        """Fetch recent conversations for the history view (async)."""
        lister = getattr(self._pipeline, "list_chats", None)
        if lister is None:  # demo pipeline has no persistence
            self.chatsListed.emit([])
            return

        async def call():
            result = lister(limit)
            return await result if inspect.isawaitable(result) else result

        self._worker.submit(call()).add_done_callback(self._chatsReady.emit)

    @Slot(str)
    def loadChat(self, chat_id: str) -> None:
        """Open a stored conversation: replay its transcript and continue it."""
        if not chat_id:
            return
        getter = getattr(self._pipeline, "get_messages", None)
        if getter is None:
            return

        async def call():
            result = getter(chat_id)
            return await result if inspect.isawaitable(result) else result

        self._worker.submit(call()).add_done_callback(
            lambda fut: self._messagesReady.emit(fut, chat_id)
        )

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

    @Slot(object)
    def _on_chats(self, fut: Future) -> None:
        try:
            chats = fut.result()
        except Exception as exc:
            self.errorRaised.emit(str(exc) or exc.__class__.__name__)
            return
        self.chatsListed.emit(
            [
                {
                    "id": str(getattr(c, "id", "")),
                    "preview": getattr(c, "preview", "") or "",
                    "count": int(getattr(c, "message_count", 0) or 0),
                    "updated": _format_timestamp(getattr(c, "updated_at", None)),
                }
                for c in chats
            ]
        )

    @Slot(object, str)
    def _on_messages(self, fut: Future, chat_id: str) -> None:
        try:
            messages = fut.result()
        except Exception as exc:
            self.errorRaised.emit(str(exc) or exc.__class__.__name__)
            return
        # Continue this conversation from now on.
        from uuid import UUID

        try:
            self._chat_id = UUID(chat_id)
        except (ValueError, TypeError):
            self._chat_id = chat_id
        transcript = [
            {
                "role": getattr(m, "role", "assistant").value
                if hasattr(getattr(m, "role", None), "value")
                else str(getattr(m, "role", "assistant")),
                "text": getattr(m, "content", ""),
            }
            for m in messages
        ]
        self.chatLoaded.emit(chat_id, transcript)


class SettingsBackend(QObject):
    currentThemeChanged = Signal()
    themesChanged = Signal()
    currentCharacterChanged = Signal()
    charactersChanged = Signal()
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
        character_store: CharacterStore | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self._worker, self._root, self._chat, self._theme = worker, root, chat, theme
        self._character_store = character_store
        self._built_in_ids = {c.character_id for c in root.config.characters}
        self._characters = list(root.config.characters)
        if self._character_store is not None:
            for info in self._character_store.load():
                if not any(
                    c.character_id == info.character_id for c in self._characters
                ):
                    self._characters.append(info)
        self._current = character.character_id
        self._busy = False
        self._built.connect(self._on_built)
        self._theme.themesChanged.connect(self.themesChanged.emit)

    # --- theme management ----------------------------------------------
    @Property("QStringList", notify=themesChanged)
    def themes(self):
        return list(self._theme.themes)

    @Property(str, notify=currentThemeChanged)
    def currentTheme(self):
        return self._theme.themeId

    @Property("QStringList", constant=True)
    def colorTokens(self):
        return list(REQUIRED_TOKENS)

    @Slot(str)
    def selectTheme(self, theme_id: str) -> None:
        if theme_id not in self._theme.themes:
            return
        self._theme.setTheme(theme_id)
        self.currentThemeChanged.emit()
        self.themeApplied.emit(theme_id)

    @Slot(str, str, bool, "QVariantMap", result=str)
    def saveTheme(self, theme_id: str, name: str, dark: bool, colors) -> str:
        """Create/update a custom theme; returns the id or '' on failure."""
        saved = self._theme.saveCustomTheme(theme_id, name, dark, dict(colors))
        if saved:
            self.currentThemeChanged.emit()
            self.themeApplied.emit(saved)
        return saved

    @Slot(str, result=bool)
    def deleteTheme(self, theme_id: str) -> bool:
        removed = self._theme.deleteCustomTheme(theme_id)
        if removed:
            self.currentThemeChanged.emit()
        return removed

    @Slot(str, result="QVariantMap")
    def themeColors(self, theme_id: str):
        # Route through the controller so optional tokens (e.g. ``text``) are
        # backfilled for built-in/custom themes that predate them.
        return self._theme.resolved_colors(theme_id)

    # --- character management ------------------------------------------
    @Property("QStringList", notify=charactersChanged)
    def characters(self):
        return [c.character_id for c in self._characters]

    @Property(str, notify=currentCharacterChanged)
    def currentCharacter(self):
        return self._current

    @Property(bool, notify=busyChanged)
    def busy(self):
        return self._busy

    @Slot(str)
    def selectCharacter(self, character_id: str) -> None:
        if self._busy or character_id == self._current:
            return
        info = self._find(character_id)
        if info is None:
            return
        self._set_busy(True)
        self._rebuild(info, character_id)

    @Slot("QVariantMap", result=str)
    def saveCharacter(self, data) -> str:
        """Create or update a character and select it.

        ``data`` mirrors the Settings form: name, personality, greeting, id of
        the edited character (optional), and a map of expression -> asset path.
        Returns the resulting character id, or '' on validation error.
        """
        from src.ai_girlfriend.models.character import CharacterInfo

        name = (data.get("name") or "").strip()
        if not name:
            return ""
        photo = {
            str(k): str(v) for k, v in (data.get("photo_emoji_map") or {}).items() if v
        }
        try:
            info = CharacterInfo(
                name=name,
                personality=str(data.get("personality") or ""),
                greeting_message=str(data.get("greeting_message") or ""),
                photo_emoji_map=photo,
                initial_expression=str(data.get("initial_expression") or "default"),
                temperature=_optional_float(data.get("temperature")),
                max_tokens=_optional_int(data.get("max_tokens")),
            )
        except Exception as exc:
            self._chat.errorRaised.emit(str(exc) or exc.__class__.__name__)
            return ""

        new_id = info.character_id
        original_id = data.get("original_id")
        # Replace the edited character in-place (keep its list position).
        for i, c in enumerate(self._characters):
            if c.character_id == (original_id or new_id):
                self._characters[i] = info
                break
        else:
            self._characters.append(info)

        if original_id and original_id != new_id:
            self._current = new_id if self._current == original_id else self._current
        self._persist_characters()
        self.charactersChanged.emit()
        self._set_busy(True)
        self._rebuild(info, new_id)
        return new_id

    @Slot(str, result=bool)
    def deleteCharacter(self, character_id: str) -> bool:
        """Delete a custom character (built-ins cannot be removed)."""
        if character_id in self._built_in_ids:
            return False
        before = len(self._characters)
        self._characters = [
            c for c in self._characters if c.character_id != character_id
        ]
        if len(self._characters) == before:
            return False
        self._persist_characters()
        self.charactersChanged.emit()
        if self._current == character_id and self._characters:
            self.selectCharacter(self._characters[0].character_id)
        return True

    @Slot(result="QVariantMap")
    def newCharacterTemplate(self):
        return {
            "name": "",
            "personality": "",
            "greeting_message": "",
            "initial_expression": "default",
            "temperature": "",
            "max_tokens": "",
            "photo_emoji_map": {},
        }

    @Slot(str, result="QVariantMap")
    def characterPhotos(self, character_id: str):
        c = self._find(character_id)
        if c is None:
            return {}
        return dict(getattr(c, "photo_emoji_map", {}) or {})

    # --- view helpers (display data for the pickers) --------------------
    @Slot(str, result="QVariantMap")
    def themeInfo(self, theme_id: str):
        t = self._theme.themes.get(theme_id) or THEMES.get(theme_id)
        if t is None:
            return {}
        c = t["colors"]
        return {
            "name": t["name"],
            "dark": t["dark"],
            "custom": bool(t.get("custom")),
            "primary": c["primary"],
            "secondary": c["secondary"],
            "background": c["background"],
        }

    @Slot(str, result="QVariantMap")
    def characterInfo(self, character_id: str):
        c = self._find(character_id)
        if c is None:
            return {}
        expr = getattr(c, "initial_expression", "neutral")
        temperature = getattr(c, "temperature", None)
        max_tokens = getattr(c, "max_tokens", None)
        return {
            "name": c.name,
            "personality": getattr(c, "personality", "") or "",
            "greeting_message": _character_greeting(c),
            "expression": expr,
            "temperature": "" if temperature is None else temperature,
            "max_tokens": "" if max_tokens is None else max_tokens,
            "custom": character_id not in self._built_in_ids,
            "thumb": _expression_url(c, expr, self._chat._pipeline),
        }

    # --- internals ------------------------------------------------------
    def _find(self, character_id: str):
        return next(
            (c for c in self._characters if c.character_id == character_id), None
        )

    def _persist_characters(self) -> None:
        if self._character_store is None:
            return
        custom = [
            c for c in self._characters if c.character_id not in self._built_in_ids
        ]
        self._character_store.save(custom)

    def _rebuild(self, info, character_id: str) -> None:
        async def build():
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                None, lambda: self._root.build_pipeline(character=info)
            )

        def done(fut: Future) -> None:
            self._built.emit(fut, character_id)

        self._worker.submit(build()).add_done_callback(done)

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
        info = self._find(character_id)
        if info is not None:
            self._current = character_id
            self._chat.apply_character(
                pipeline, info
            )  # fresh chat_id, greeting, portrait
            self.currentCharacterChanged.emit()
            self.characterChanged.emit(character_id)
        self._set_busy(False)
