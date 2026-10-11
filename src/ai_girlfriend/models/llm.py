"""Domain models and contracts for text generation (LLM).

The pipeline speaks to providers through the normalized ``GenerationRequest`` /
``GenerationResponse`` pair and the typed ``StreamEvent`` stream. No provider
library types ever leak into the core (see spec, section 6.1).
"""

from collections.abc import AsyncIterator
from datetime import datetime
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from src.ai_girlfriend.models.events import StreamEvent


class Role(StrEnum):
    """The role of the author of a message."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class Message(BaseModel):
    """A single message within a conversation."""

    id: UUID = Field(
        default_factory=uuid4,
        description="The unique identifier for the message.",
    )
    conversation_id: UUID = Field(
        description="The unique identifier for the conversation.",
    )
    role: Role = Field(description="The role of the message sender.")
    content: str = Field(description="The content of the message.")
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="The timestamp when the message was created.",
    )


class GenerationRequest(BaseModel):
    """A normalized request sent to an ``ILLMProvider``."""

    messages: list[Message] = Field(
        description="The ordered conversation passed to the model."
    )
    model: str = Field(description="The model to be used by the provider.")
    params: dict[str, Any] = Field(
        default_factory=dict,
        description="Sampling parameters (temperature, top_p, ...).",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Free-form metadata (character id, request id, ...).",
    )


class GenerationResponse(BaseModel):
    """A normalized response returned by an ``ILLMProvider``."""

    content: str = Field(description="The generated text.")
    usage: dict[str, int] = Field(
        default_factory=dict,
        description="Token usage counters, if the provider reports them.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Provider-specific metadata.",
    )


@runtime_checkable
class ILLMProvider(Protocol):
    """Contract for LLM providers.

    Implementations translate provider-specific errors into the domain error
    hierarchy and never expose their client library objects.
    """

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate a full response in one call."""
        ...

    def stream(self, request: GenerationRequest) -> AsyncIterator[StreamEvent]:
        """Stream the response as a typed event sequence."""
        ...


__all__ = [
    "GenerationRequest",
    "GenerationResponse",
    "ILLMProvider",
    "Message",
    "Role",
]
