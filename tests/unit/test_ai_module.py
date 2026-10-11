"""Unit tests for the AI module (AIController, providers, streaming events)."""

from uuid import uuid4

import pytest

from src.ai_girlfriend.exc import GenerationTimeoutError, ProviderError
from src.ai_girlfriend.llm.llm_provider import AIController, LLMProviderFactory
from src.ai_girlfriend.models.events import Done, TextDelta
from src.ai_girlfriend.models.events import Error as ErrorEvent
from src.ai_girlfriend.models.llm import (
    GenerationRequest,
    GenerationResponse,
    Message,
    Role,
)
from src.ai_girlfriend.testing.fake_llm import FakeLLMProvider


def make_request() -> GenerationRequest:
    return GenerationRequest(
        messages=[Message(conversation_id=uuid4(), role=Role.USER, content="Hi!")],
        model="test-model",
    )


async def test_controller_generate_returns_response():
    provider = FakeLLMProvider(response="Hello there")
    controller = AIController(provider)

    result = await controller.generate(make_request())

    assert isinstance(result, GenerationResponse)
    assert result.content == "Hello there"
    assert len(provider.requests) == 1


async def test_controller_wraps_unexpected_errors_as_provider_error():
    provider = FakeLLMProvider(error=RuntimeError("boom"))
    controller = AIController(provider)

    with pytest.raises(ProviderError):
        await controller.generate(make_request())


async def test_controller_streams_typed_events():
    provider = FakeLLMProvider(chunks=["Hel", "lo", "!"])
    controller = AIController(provider)

    events = [event async for event in controller.stream(make_request())]

    deltas = [e for e in events if isinstance(e, TextDelta)]
    assert [d.text for d in deltas] == ["Hel", "lo", "!"]
    assert isinstance(events[-1], Done)


async def test_controller_stream_emits_error_event_then_raises():
    provider = FakeLLMProvider(error=RuntimeError("nope"))
    controller = AIController(provider)

    events = []
    with pytest.raises(ProviderError):
        async for event in controller.stream(make_request()):
            events.append(event)

    assert any(isinstance(e, ErrorEvent) for e in events)


async def test_controller_timeout_is_wrapped():
    import asyncio

    async def slow_generate(request):
        await asyncio.sleep(1)
        return GenerationResponse(content="late")

    provider = FakeLLMProvider()
    provider.generate = slow_generate  # type: ignore[assignment]
    controller = AIController(provider, request_timeout=0.01)

    with pytest.raises(GenerationTimeoutError):
        await controller.generate(make_request())


def test_factory_creates_ollama_provider():
    provider = LLMProviderFactory.create_provider(
        "ollama", model="llama3", url="http://localhost:11434"
    )

    assert provider.provider == "ollama"
    assert provider.model == "llama3"


def test_factory_rejects_unknown_provider():
    with pytest.raises(ProviderError):
        LLMProviderFactory.create_provider("unknown", model="x")


def test_factory_requires_api_key_for_deepseek():
    with pytest.raises(ProviderError):
        LLMProviderFactory.create_provider("deepseek", model="x", api_key=None)
