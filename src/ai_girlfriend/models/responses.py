"""High-level response models returned by the pipeline facade."""

from pydantic import BaseModel, Field


class CharacterResponse(BaseModel):
    """A normalized reply from the companion, ready for any adapter."""

    text: str = Field(description="The generated reply text.")
    expression: str = Field(
        description="A validated expression id from the character's dictionary."
    )


__all__ = ["CharacterResponse"]
