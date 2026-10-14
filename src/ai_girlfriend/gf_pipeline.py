"""The pipeline facade.

``GfPipeline`` coordinates the AI controller, the memory manager, and the
expression manager. It is a facade, not a god object: it contains no SQL, no
HTTP, and no GUI logic (see spec, sections 2 and 8).
"""

import json
from collections.abc import AsyncIterator
from typing import Any
from uuid import UUID, uuid4

from src.ai_girlfriend.character.expression_manager import ExpressionManager
from src.ai_girlfriend.database.memory_manager import MemoryManager
from src.ai_girlfriend.llm.llm_provider import AIController
from src.ai_girlfriend.models.character import CharacterInfo
from src.ai_girlfriend.models.events import Done, Error, StreamEvent, TextDelta
from src.ai_girlfriend.models.llm import GenerationRequest, Message, Role
from src.ai_girlfriend.models.responses import CharacterResponse


class GfPipeline:
    """Public facade of the companion core."""

    def __init__(
        self,
        gf_config: CharacterInfo,
        ai_controller: AIController,
        memory_manager: MemoryManager,
        expression_manager: ExpressionManager,
        default_temperature: float | None = None,
        default_max_tokens: int | None = None,
    ):
        self.gf_config = gf_config
        self.ai_controller = ai_controller
        self.memory_manager = memory_manager
        self.expression_manager = expression_manager
        self.default_temperature = default_temperature
        self.default_max_tokens = default_max_tokens
        self._initialized = False

    async def init(self) -> None:
        """Initialize resources owned by the pipeline (idempotent)."""
        if self._initialized:
            return
        await self.memory_manager.database.init()
        self._initialized = True

    # -- request building -------------------------------------------------

    def _generation_params(self) -> dict[str, Any]:
        """Sampling params: the character's own overrides beat the defaults.

        Falls back to the pipeline defaults (which come from the global
        ``Config``) and translates the token cap to the provider's key name
        (``num_predict`` for Ollama, ``max_tokens`` for OpenAI-compatible APIs).
        """
        provider = getattr(self.ai_controller.provider, "provider", "") or "ollama"
        return self.gf_config.generation_params(
            temperature=self.default_temperature,
            max_tokens=self.default_max_tokens,
            provider=provider,
        )

    def _build_request(self, context_messages: list[Message]) -> GenerationRequest:
        system_message = Message(
            conversation_id=context_messages[0].conversation_id
            if context_messages
            else uuid4(),
            role=Role.SYSTEM,
            content=self.gf_config.system_prompt,
        )
        return GenerationRequest(
            messages=[system_message, *context_messages],
            model=getattr(self.ai_controller.provider, "model", ""),
            params=self._generation_params(),
            metadata={"character_id": self.gf_config.character_id},
        )

    @staticmethod
    def _parse_response(raw: str) -> tuple[str, str | None]:
        """Extract ``(text, expression)`` from the model's structured output.

        The prompt asks for ``{"text": ..., "emotion": ...}`` but the legacy
        ``expression`` key is accepted too, so older clients keep working. If
        parsing fails, the raw text is used and the expression is left to fall
        back to ``initial_expression`` (see spec, section 6.1).
        """
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return raw, None
        if not isinstance(data, dict):
            return raw, None
        text = data.get("text")
        if not isinstance(text, str):
            return raw, None
        expression = data.get("emotion", data.get("expression"))
        return text, expression if isinstance(expression, str) else None

    # -- public API -------------------------------------------------------

    async def chat(
        self, message: str, chat_id: UUID | None = None
    ) -> CharacterResponse:
        """Process a message and return a normalized ``CharacterResponse``."""
        if not self._initialized:
            await self.init()

        conversation_id = await self._ensure_chat(chat_id)
        user_message = Message(
            conversation_id=conversation_id, role=Role.USER, content=message
        )

        bundle = await self.memory_manager.build_context(conversation_id, user_message)
        request = self._build_request([*bundle.messages, user_message])

        generation = await self.ai_controller.generate(request)

        text, expression_id = self._parse_response(generation.content)
        expression = self.expression_manager.resolve(expression_id)

        bot_message = Message(
            conversation_id=conversation_id, role=Role.ASSISTANT, content=text
        )
        await self.memory_manager.record_exchange(user_message, bot_message)

        return CharacterResponse(
            text=text, expression=expression, chat_id=conversation_id
        )

    async def stream_chat(
        self, message: str, chat_id: UUID | None = None
    ) -> AsyncIterator[StreamEvent]:
        """Stream a response as typed events.

        The exchange is saved only on ``Done``; partial text from a cancelled
        stream is not persisted (see spec, section 8).
        """
        if not self._initialized:
            await self.init()

        conversation_id = await self._ensure_chat(chat_id)
        user_message = Message(
            conversation_id=conversation_id, role=Role.USER, content=message
        )
        bundle = await self.memory_manager.build_context(conversation_id, user_message)
        request = self._build_request([*bundle.messages, user_message])

        collected: list[str] = []
        async for event in self.ai_controller.stream(request):
            if isinstance(event, TextDelta):
                collected.append(event.text)
                yield event
            elif isinstance(event, Done):
                raw = "".join(collected)
                text, _ = self._parse_response(raw)
                bot_message = Message(
                    conversation_id=conversation_id,
                    role=Role.ASSISTANT,
                    content=text,
                )
                await self.memory_manager.record_exchange(user_message, bot_message)
                yield event
            elif isinstance(event, Error):
                yield event

    async def _ensure_chat(self, chat_id: UUID | None) -> UUID:
        """Return an existing chat id, or create a new chat row.

        A ``None`` chat id means "first message of a new conversation". We must
        create the ``chats`` row before saving messages, otherwise the messages'
        foreign key (``chat_id -> chats.id``) fails.
        """
        if chat_id is not None:
            return chat_id
        return await self.memory_manager.create_chat()

    # -- history (read-only views for the UI) -----------------------------

    async def list_chats(self, limit: int = 50):
        """List recent conversations (newest first) for the history view."""
        if not self._initialized:
            await self.init()
        return await self.memory_manager.list_chats(limit)

    async def get_messages(self, chat_id: UUID) -> list[Message]:
        """Return the full stored history of a chat, oldest first."""
        if not self._initialized:
            await self.init()
        return await self.memory_manager.get_messages(chat_id)

    async def close(self) -> None:
        """Release resources held by the pipeline."""
        await self.memory_manager.database.close()
        self._initialized = False


__all__ = ["GfPipeline"]
