"""The composition root: the single place where dependencies are assembled.

Factories are called only here. Controllers and the pipeline receive ready-made
providers through their constructors (see spec, sections 2 and 7).
"""

from pathlib import Path

from src.ai_girlfriend.character.expression_manager import ExpressionManager
from src.ai_girlfriend.config.config import Config
from src.ai_girlfriend.database.conversation_window import ConversationWindowProvider
from src.ai_girlfriend.database.database_controller import DatabaseController
from src.ai_girlfriend.database.database_factory import DatabaseFactory
from src.ai_girlfriend.database.memory_manager import MemoryManager
from src.ai_girlfriend.exc import ConfigError
from src.ai_girlfriend.gf_pipeline import GfPipeline
from src.ai_girlfriend.llm.llm_provider import AIController, LLMProviderFactory
from src.ai_girlfriend.models.character import CharacterInfo


class CompositionRoot:
    """Builds a fully wired ``GfPipeline`` from configuration."""

    def __init__(self, config: Config):
        self.config = config

    def build_pipeline(self, character: CharacterInfo | None = None) -> GfPipeline:
        """Assemble the pipeline from the given settings."""
        character = character or self._select_character()

        # 1. providers via factories
        llm_provider = LLMProviderFactory.create_provider(
            provider_name=self.config.provider,
            model=self.config.model,
            url=self.config.llm_url,
            api_key=self.config.api_key.get_secret_value()
            if self.config.api_key is not None
            else None,
        )
        db_provider = DatabaseFactory().create(
            provider=self.config.database_provider,
            url=self.config.database_url,
        )

        # 2. controllers over the providers
        ai_controller = AIController(
            llm_provider, request_timeout=self.config.request_timeout
        )
        database_controller = DatabaseController(db_provider)

        # 3. context + memory
        context_provider = ConversationWindowProvider(
            database=database_controller, window=self.config.context_window
        )
        memory_manager = MemoryManager(
            database=database_controller, context_provider=context_provider
        )

        # 4. character
        expression_manager = ExpressionManager(character, base_dir=Path("."))

        # 5. facade
        return GfPipeline(
            gf_config=character,
            ai_controller=ai_controller,
            memory_manager=memory_manager,
            expression_manager=expression_manager,
        )

    def _select_character(self) -> CharacterInfo:
        if not self.config.characters:
            raise ConfigError(
                "No characters configured. Provide at least one character."
            )
        return self.config.characters[0]


__all__ = ["CompositionRoot"]
