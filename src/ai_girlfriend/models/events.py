"""Typed streaming events emitted by LLM providers.

A single contract serves both SSE adapters (FastAPI) and future GUI adapters.
See the architecture spec, section 6.1.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, Field


class TextDelta(BaseModel):
    """A partial chunk of generated text."""

    type: Literal["text_delta"] = "text_delta"
    text: str = Field(description="The piece of text produced in this chunk.")


class Done(BaseModel):
    """Terminal event: generation finished successfully."""

    type: Literal["done"] = "done"
    usage: dict[str, int] = Field(
        default_factory=dict,
        description="Token usage counters (prompt/completion/total), if known.",
    )
    metadata: dict[str, object] = Field(
        default_factory=dict,
        description="Provider-specific metadata (model name, finish reason, ...).",
    )


class Error(BaseModel):
    """Terminal event: generation failed."""

    type: Literal["error"] = "error"
    message: str = Field(description="Human-readable error description.")
    code: str | None = Field(
        default=None,
        description="Optional machine-readable error code (e.g. 'timeout').",
    )


# A discriminated union: consumers can branch on the `type` field.
StreamEvent = Annotated[
    TextDelta | Done | Error,
    Field(discriminator="type"),
]


__all__ = ["Done", "Error", "StreamEvent", "TextDelta"]
