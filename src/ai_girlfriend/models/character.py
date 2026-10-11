"""Character profile configuration (the ``GfConfig`` of the spec).

A character carries its display name, personality, greeting, and the dictionary
of available expressions (``photo_emoji_map``). The spec-facing accessors
``character_id``, ``system_prompt``, and ``expressions`` are derived from these
fields so the rest of the core stays independent of the raw config shape.

Asset paths are validated at load time: absolute (or ``~``) paths are allowed
as-is; relative paths are resolved against the character directory and must not
escape it with ``..`` (see spec, section 5.2).
"""

from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class CharacterInfo(BaseModel):
    """Configuration of a single companion character."""

    name: str = Field(description="The display name of the character.")
    personality: str = Field(
        description="A brief description of the character's personality."
    )
    greeting_message: str = Field(
        default="",
        description="A greeting message used when interacting with users.",
    )
    photo_emoji_map: dict[str, str] = Field(
        default_factory=dict,
        description="Map of expression id -> asset path/url for the character.",
    )
    initial_expression: str = Field(
        default="default",
        description="The expression used when none is resolved.",
    )
    schema_version: int = Field(
        default=1, description="Version of the character format."
    )

    @field_validator("photo_emoji_map")
    @classmethod
    def _validate_expression_paths(cls, value: dict[str, str]) -> dict[str, str]:
        for expression_id, asset in value.items():
            if not asset:
                continue  # empty placeholder allowed (asset not defined yet)
            # Absolute paths (e.g. /home/user/Pictures/x.jpg) and ~-paths are
            # allowed: users keep their photos outside the character directory.
            path = Path(asset).expanduser()
            if path.is_absolute():
                continue
            if ".." in path.parts:
                raise ValueError(
                    f"Expression {expression_id!r} must not escape the "
                    f"character directory, got {asset!r}."
                )
        return value

    @property
    def character_id(self) -> str:
        """Stable identifier derived from the character name."""
        return self.name.strip().lower().replace(" ", "-")

    @property
    def system_prompt(self) -> str:
        """The system prompt priming the model with the character's persona."""
        return (
            f"You are {self.name}. {self.personality}\n"
            "Respond ONLY with a JSON object of the form "
            '{"text": "<your reply>", "expression": "<expression id>"}. '
            f"Available expressions: {sorted(self.expressions)}."
        )

    @property
    def expressions(self) -> dict[str, str]:
        """Non-empty expression id -> asset path mapping."""
        return {k: v for k, v in self.photo_emoji_map.items() if v}


__all__ = ["CharacterInfo"]
