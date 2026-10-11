"""High-level response models returned by the pipeline facade."""

from uuid import UUID

from pydantic import BaseModel, Field


class CharacterResponse(BaseModel):
    """A normalized reply from the companion, ready for any adapter."""

    text: str = Field(description="The generated reply text.")
    expression: str = Field(
        description="A validated expression id from the character's dictionary."
    )
    chat_id: UUID | None = Field(
        default=None,
        description="The chat the reply belongs to (created lazily if it was new).",
    )


__all__ = ["CharacterResponse"]
