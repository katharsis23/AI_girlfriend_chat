"""Domain models and contract for context assembly.

A ``ContextBundle`` keeps dialogue history and retrieved memories separate:
they are different sources with different update dynamics (see spec, section 9).
"""

from typing import Protocol, runtime_checkable
from uuid import UUID

from pydantic import BaseModel, Field

from src.ai_girlfriend.models.llm import Message


class Memory(BaseModel):
    """A selected long-term memory fact or event."""

    content: str = Field(description="The memory text.")
    source: str | None = Field(
        default=None, description="Where the memory came from (chat, document, ...)."
    )
    score: float | None = Field(
        default=None, description="Optional relevance score from retrieval."
    )


class ContextBundle(BaseModel):
    """The assembled context passed to the model."""

    messages: list[Message] = Field(
        default_factory=list, description="Recent dialogue history."
    )
    memories: list[Memory] = Field(
        default_factory=list, description="Retrieved long-term memories."
    )


@runtime_checkable
class IContextProvider(Protocol):
    """Contract for context providers (window, RAG, long-term memory, ...)."""

    async def build_context(self, query: str, chat_id: UUID) -> ContextBundle:
        """Build a context bundle for a query within a chat."""
        ...


__all__ = ["ContextBundle", "IContextProvider", "Memory"]
