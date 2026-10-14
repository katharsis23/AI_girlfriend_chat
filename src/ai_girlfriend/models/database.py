"""Domain models and contract for database storage.

``IDatabaseStorage`` is the low-level contract implemented by concrete
providers (SQLite, in-memory, ...). SQL and transactions live only inside the
providers; the core never sees them (see spec, section 6.2).
"""

from datetime import datetime
from typing import Protocol, runtime_checkable
from uuid import UUID

from pydantic import BaseModel, Field

from src.ai_girlfriend.models.llm import Message


@runtime_checkable
class IDatabaseStorage(Protocol):
    """Protocol to unify the low-level database providers' API."""

    async def init(self) -> None:
        """Check for the database, create tables and the database file."""
        ...

    async def create_chat(self) -> UUID:
        """Create a chat and return its identifier."""
        ...

    async def save_message(self, message: Message) -> UUID:
        """Persist a single message."""
        ...

    async def save_exchange(self, user_message: Message, bot_message: Message) -> None:
        """Persist a user/assistant pair atomically in one transaction."""
        ...

    async def get_recent_messages(self, chat_id: UUID, limit: int) -> list[Message]:
        """Return up to ``limit`` most recent messages of a chat, oldest first."""
        ...

    async def list_chats(self, limit: int = 50) -> list["ChatSummary"]:
        """Return recent conversations, most recently updated first."""
        ...

    async def get_messages(self, chat_id: UUID) -> list[Message]:
        """Return the full message history of a chat, oldest first."""
        ...

    async def close(self) -> None:
        """Release underlying resources."""
        ...


class ChatSummary(BaseModel):
    """A lightweight row describing a conversation for the history list."""

    id: UUID = Field(description="UUID of the chat instance.")
    updated_at: datetime = Field(description="The last edited time.")
    message_count: int = Field(default=0, description="Number of stored messages.")
    preview: str = Field(
        default="", description="A short preview of the last message, for the list."
    )


class Chat(BaseModel):
    """A conversation between the user and the companion."""

    id: UUID = Field(description="UUID of the chat instance.")
    content: list[Message] = Field(default_factory=list, description="Chat history.")
    summary: Message | None = Field(
        default=None,
        description="Optional summary used to economize the context window.",
    )
    updated_at: datetime = Field(description="The last edited time.")


__all__ = ["Chat", "ChatSummary", "IDatabaseStorage"]
