"""Coordinates context assembly and exchange persistence.

``MemoryManager`` is the single point the pipeline talks to for memory. It
depends on ``DatabaseController`` (not on a concrete database) and on an
``IContextProvider`` (see spec, sections 4 and 6.3).
"""

from uuid import UUID

from src.ai_girlfriend.database.database_controller import DatabaseController
from src.ai_girlfriend.models.context import ContextBundle, IContextProvider
from src.ai_girlfriend.models.llm import Message


class MemoryManager:
    """Builds context bundles and records exchanges."""

    def __init__(
        self, database: DatabaseController, context_provider: IContextProvider
    ):
        self.database = database
        self.context_provider = context_provider

    async def create_chat(self) -> UUID:
        """Create a new chat and return its identifier.

        Called by the pipeline when a message arrives without a ``chat_id`` so
        the row referenced by the messages' foreign key exists (see spec,
        section 6.2).
        """
        return await self.database.create_chat()

    async def build_context(
        self, chat_id: UUID, user_message: Message
    ) -> ContextBundle:
        """Assemble the context (history + memories) for the given message."""
        return await self.context_provider.build_context(
            query=user_message.content, chat_id=chat_id
        )

    async def record_exchange(
        self, user_message: Message, bot_message: Message
    ) -> None:
        """Persist the user and assistant messages in a single transaction."""
        await self.database.save_exchange(user_message, bot_message)

    async def list_chats(self, limit: int = 50):
        """List recent conversations for the history view."""
        return await self.database.list_chats(limit)

    async def get_messages(self, chat_id: UUID) -> list[Message]:
        """Return the full stored history of a chat, oldest first."""
        return await self.database.get_messages(chat_id)


__all__ = ["MemoryManager"]
