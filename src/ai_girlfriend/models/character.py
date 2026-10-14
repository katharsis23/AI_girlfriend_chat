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
    temperature: float | None = Field(
        default=None,
        ge=0.0,
        le=2.0,
        description=(
            "Sampling temperature for this character (0 = deterministic, "
            "higher = more creative). ``None`` falls back to the global config."
        ),
    )
    max_tokens: int | None = Field(
        default=None,
        gt=0,
        description=(
            "Approximate cap on the number of tokens the model may generate "
            "in one reply. ``None`` falls back to the global config."
        ),
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
    def available_emotions(self) -> list[str]:
        """The emotion ids the model is allowed to choose from.

        Falls back to the initial expression when no asset is mapped yet, so
        the model always receives a non-empty, valid set to pick from.
        """
        emotions = sorted(self.expressions)
        if not emotions:
            emotions = [self.initial_expression]
        return emotions

    @property
    def system_prompt(self) -> str:
        """The system prompt priming the model with the character's persona.

        The prompt lists the *exact* ``available_emotions`` and forces the model
        to answer with a strict JSON object so the UI can pick a portrait. This
        steers the model away from hallucinating emotion ids or free-form text
        (see spec, section 6.1).
        """
        emotions = self.available_emotions
        return (
            f"You are {self.name}. {self.personality}\n"
            "You MUST reply with a single JSON object and nothing else, in this "
            'exact shape: {"text": "<your reply>", "emotion": "<emotion id>"}.\n'
            f'"text" is your reply to the user, in character, as plain text.\n'
            f'"emotion" MUST be exactly one of the available_emotions: '
            f"{emotions}. Never invent new values; if unsure, use "
            f"{self.initial_expression!r}.\n"
            "Do not wrap the JSON in markdown fences and do not add any text "
            "outside the JSON object."
        )

    @property
    def expressions(self) -> dict[str, str]:
        """Non-empty expression id -> asset path mapping."""
        return {k: v for k, v in self.photo_emoji_map.items() if v}

    def generation_params(
        self,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        provider: str = "ollama",
    ) -> dict[str, float | int]:
        """Sampling parameters for ``GenerationRequest.params``.

        The character's own ``temperature`` / ``max_tokens`` win over the
        passed-in defaults (which come from the global ``Config``). Keys are
        only included when they resolve to a value, so providers keep their own
        defaults otherwise.

        The token-cap key differs per provider: Ollama expects ``num_predict``
        while OpenAI-compatible APIs (DeepSeek) expect ``max_tokens``.
        """
        resolved_temperature = (
            self.temperature if self.temperature is not None else temperature
        )
        resolved_max_tokens = (
            self.max_tokens if self.max_tokens is not None else max_tokens
        )
        params: dict[str, float | int] = {}
        if resolved_temperature is not None:
            params["temperature"] = resolved_temperature
        if resolved_max_tokens is not None:
            key = "num_predict" if provider == "ollama" else "max_tokens"
            params[key] = resolved_max_tokens
        return params


__all__ = ["CharacterInfo"]
