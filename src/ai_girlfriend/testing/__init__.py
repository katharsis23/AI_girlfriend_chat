"""Test fakes shipped with the package (see spec, section 11)."""

from src.ai_girlfriend.testing.fake_llm import FakeLLMProvider
from src.ai_girlfriend.testing.in_memory_db import InMemoryDatabaseProvider

__all__ = ["FakeLLMProvider", "InMemoryDatabaseProvider"]
