"""Unit tests for the composition root wiring."""

import pytest

from src.ai_girlfriend.composition_root import CompositionRoot
from src.ai_girlfriend.config.config import Config
from src.ai_girlfriend.database.sqlite_provider import SQLiteProvider
from src.ai_girlfriend.exc import ConfigError
from src.ai_girlfriend.gf_pipeline import GfPipeline
from src.ai_girlfriend.llm.ollama_provider import OllamaProvider
from src.ai_girlfriend.models.character import CharacterInfo

pytestmark = pytest.mark.unit


def character_dict() -> dict:
    return {
        "name": "Aria",
        "personality": "A warm companion.",
        "greeting_message": "Hi!",
        "photo_emoji_map": {"neutral": "neutral.png"},
        "initial_expression": "neutral",
    }


def make_config(**overrides) -> Config:
    defaults = {
        "LLM_PROVIDER": "ollama",
        "LLM_URL": "http://localhost:11434",
        "LLM_MODEL": "llama3",
        "DATABASE_PROVIDER": "sqlite",
        "DATABASE_URL": "sqlite:///./test.db",
        "CONTEXT_WINDOW": 5,
        "REQUEST_TIMEOUT": 30.0,
        "CHARACTERS": [CharacterInfo.model_validate(character_dict())],
    }
    defaults.update(overrides)
    return Config(**defaults)


def test_build_pipeline_wires_all_dependencies():
    config = make_config()
    pipeline = CompositionRoot(config).build_pipeline()

    assert isinstance(pipeline, GfPipeline)
    assert isinstance(pipeline.ai_controller.provider, OllamaProvider)
    assert pipeline.ai_controller.request_timeout == 30.0
    assert isinstance(pipeline.memory_manager.database.provider, SQLiteProvider)
    assert pipeline.memory_manager.context_provider.window == 5
    assert pipeline.gf_config.character_id == "aria"


def test_build_pipeline_requires_a_character():
    config = make_config(CHARACTERS=[])
    with pytest.raises(ConfigError):
        CompositionRoot(config).build_pipeline()
