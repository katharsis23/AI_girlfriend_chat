from typing import Protocol
import asyncio
from uuid import UUID
from pydantic import Field, BaseModel
from src.ai_girlfriend.models.llm import Message
from datetime import datetime


class IDatabaseStorage(Protocol):
    """Protocol to unify the Low-Level DBProviders API"""


    async def init(self):
        """
        Checks for database in db path, creates tables and database
        """
        ...


    async def create_chat(self) -> UUID:
        """
        Creates chat in database and returns uuid of instance
        """
        ...

    async def save_message(self, message: str, chat_id: UUID) -> UUID:
        """
        Creates message instance in database
        """
        ...

    async def save_exchange(self, user_message: str, bot_message: str):
        ...

    async def get_chat_message(self, chat_id: UUID) -> list:
        ...


    async def get_recent_messages(self):
        """Returns chat history of the last edited chat"""


    async def _close():
        ...


class Chat(BaseModel):
    id: UUID = Field(
        description="UUID of chat instance"
    )
    content: list[Message] = Field(
        description="List of Messages: Chat history"
    )
    summary: Message | None = Field(
        description="In future we will add to sumarize the chat to econom the context space"
    )
    updated_at: datetime = Field(
        description="The last edited time"
    )
    # Consider adding additional fields


# ========= Context ===========

class ContextBundle(BaseModel):
    messages: list[Message] = Field(
        description="Content"
    )

class IContextProvider(BaseModel):
    async def build_context(self, query, chat_id: UUID) -> ContextBundle:
        ...

class ConversationWindowProvider(BaseModel):
    database
    window