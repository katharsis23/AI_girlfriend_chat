"""Application configuration.

Settings are loaded from a single ``config.json`` file (see ``config.json`` at
the project root) using pydantic-settings' ``JsonConfigSettingsSource``. The
JSON holds both the global settings and the list of character profiles.
"""

from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import (
    BaseSettings,
    JsonConfigSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from src.ai_girlfriend.models.character import CharacterInfo

# Root of the project (…/src/ai_girlfriend/config/config.py -> project root).
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_CONFIG_JSON = _PROJECT_ROOT / "config.json"


class Config(BaseSettings):
    """
    Configuration class for the AI Girlfriend application.
    Reads all values from ``config.json`` via pydantic-settings.
    """

    # LLM config
    provider: Literal["ollama", "deepseek"] = Field(
        alias="LLM_PROVIDER",
        default="ollama",
        description="The provider for the LLM (Large Language Model).",
    )

    llm_url: str = Field(
        alias="LLM_URL",
        default="http://localhost:11434",
        description="The URL for the LLM provider.",
    )

    model: str = Field(
        alias="LLM_MODEL",
        default="mistral-nemo:12b-instruct-2407-q4_0",
        description="The model to be used by the LLM provider.",
    )

    api_key: SecretStr | None = Field(
        alias="LLM_API_KEY",
        default=None,
        description="The API key for the LLM provider, if required.",
    )

    # Generation / context limits
    context_window: int = Field(
        alias="CONTEXT_WINDOW",
        default=20,
        description="Number of recent messages passed to the model as context.",
    )

    request_timeout: float = Field(
        alias="REQUEST_TIMEOUT",
        default=120.0,
        description="Timeout in seconds for a single LLM request.",
    )

    # Database config
    database_provider: Literal["sqlite", "postgresql"] = Field(
        alias="DATABASE_PROVIDER",
        default="sqlite",
        description="The provider for the database.",
    )

    database_url: str = Field(
        alias="DATABASE_URL",
        default="sqlite:///./ai_girlfriend.db",
        description="The URL for the database connection.",
    )

    # Character config: a real list of profiles, straight from the JSON file.
    characters: list[CharacterInfo] = Field(
        alias="CHARACTERS",
        default_factory=list,
        description="List of character profiles loaded from config.json.",
    )

    model_config = SettingsConfigDict(
        json_file=_CONFIG_JSON,
        json_file_encoding="utf-8",
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # Precedence: explicit kwargs > config.json > env vars.
        return (
            init_settings,
            JsonConfigSettingsSource(settings_cls),
            env_settings,
        )


config = Config()
