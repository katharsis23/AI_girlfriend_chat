from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.ai_girlfriend.models.character import CharacterInfo


class Config(BaseSettings):
    """
    Configuration class for the AI Girlfriend application.
    This class uses Pydantic's BaseSettings to manage application settings.
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
    )  # Normalize and unify that both LocalUrl and HTTPUrl are supported, and that the database_url can be either a local file path or a full database URL.

    # Character config
    characters: list[CharacterInfo] = Field(
        alias="CHARACTERS",
        default=[],
        description="A list of character information for the AI Girlfriend application.",
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

config=Config()