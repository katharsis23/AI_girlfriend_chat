"""High-level wrapper over the low-level ``IDatabaseStorage`` API.

The controller is the application-layer boundary for persistence: it exists so
the rest of the core depends on a stable, provider-agnostic surface (dependency
inversion). If it ever turns out to be an empty pass-through, it should be
merged into the provider (spec, principle 10).
"""

from uuid import UUID

from src.ai_girlfriend.models.database import IDatabaseStorage
from src.ai_girlfriend.models.llm import Message


class DatabaseController:
    """Coordinates database operations behind a provider-agnostic API."""

    def __init__(self, provider: IDatabaseStorage):
        self.provider = provider

    async def init(self) -> None:
        """Initialize the underlying provider."""
        await self.provider.init()

    async def create_chat(self) -> UUID:
        """Create a new chat and return its identifier."""
        return await self.provider.create_chat()

    async def save_message(self, message: Message) -> UUID:
        """Persist a single message."""
        return await self.provider.save_message(message)

    async def save_exchange(self, user_message: Message, bot_message: Message) -> None:
        """Persist a user/assistant pair atomically."""
        await self.provider.save_exchange(user_message, bot_message)

    async def get_recent_messages(self, chat_id: UUID, limit: int) -> list[Message]:
        """Return recent messages of a chat, oldest first."""
        return await self.provider.get_recent_messages(chat_id, limit)

    async def list_chats(self, limit: int = 50):
        """Return recent conversations, most recently updated first."""
        return await self.provider.list_chats(limit)

    async def get_messages(self, chat_id: UUID) -> list[Message]:
        """Return the full message history of a chat, oldest first."""
        return await self.provider.get_messages(chat_id)

    async def close(self) -> None:
        """Close the underlying provider."""
        await self.provider.close()


__all__ = ["DatabaseController"]
