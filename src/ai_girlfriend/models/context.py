from src.ai_girlfriend.database.database_controller import DatabaseController
from pydantic import Field, BaseModel
from src.ai_girlfriend.models.llm import Message
from uuid import UUID
from typing import Protocol



class ContextBundle(BaseModel):
    messages: list[Message] = Field(
        description="Content"
    )

class IContextProvider(BaseModel):
    async def build_context(self, query, chat_id: UUID) -> ContextBundle:
        ...

class ConversationWindowProvider(BaseModel):
    database: DatabaseController
    window: int


class RAGContextProvider(Protocol):
    """Stub for now. Implement in future"""