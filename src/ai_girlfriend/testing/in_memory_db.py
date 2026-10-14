"""An in-memory ``IDatabaseStorage`` implementation for unit tests."""

from datetime import datetime
from uuid import UUID, uuid4

from src.ai_girlfriend.models.database import ChatSummary
from src.ai_girlfriend.models.llm import Message


class InMemoryDatabaseProvider:
    """Stores chats and messages in plain dicts; no I/O, no transactions."""

    def __init__(self, fail_on_save: bool = False):
        self._chats: set[UUID] = set()
        self._messages: dict[UUID, list[Message]] = {}
        self.fail_on_save = fail_on_save

    async def init(self) -> None:
        return None

    async def create_chat(self) -> UUID:
        chat_id = uuid4()
        self._chats.add(chat_id)
        self._messages[chat_id] = []
        return chat_id

    async def save_message(self, message: Message) -> UUID:
        if self.fail_on_save:
            raise RuntimeError("save disabled for this test")
        self._messages.setdefault(message.conversation_id, []).append(message)
        return message.id

    async def save_exchange(self, user_message: Message, bot_message: Message) -> None:
        if self.fail_on_save:
            raise RuntimeError("save disabled for this test")
        chat = self._messages.setdefault(user_message.conversation_id, [])
        chat.append(user_message)
        chat.append(bot_message)

    async def get_recent_messages(self, chat_id: UUID, limit: int) -> list[Message]:
        messages = self._messages.get(chat_id, [])
        return messages[-limit:]

    async def list_chats(self, limit: int = 50) -> list[ChatSummary]:
        summaries = [
            ChatSummary(
                id=chat_id,
                updated_at=(messages[-1].created_at if messages else datetime.min),
                message_count=len(messages),
                preview=(messages[-1].content[:120] if messages else ""),
            )
            for chat_id, messages in self._messages.items()
        ]
        summaries.sort(key=lambda s: s.updated_at, reverse=True)
        return summaries[:limit]

    async def get_messages(self, chat_id: UUID) -> list[Message]:
        return list(self._messages.get(chat_id, []))

    async def close(self) -> None:
        return None


__all__ = ["InMemoryDatabaseProvider"]
