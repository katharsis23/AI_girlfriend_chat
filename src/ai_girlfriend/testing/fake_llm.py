"""A deterministic in-memory ``ILLMProvider`` for unit tests.

It records the requests it receives and returns either a fixed response, a
canned stream, or raises a configured error. No network, disk, or sleep.
"""

from collections.abc import AsyncIterator, Callable

from src.ai_girlfriend.models.events import Done, StreamEvent, TextDelta
from src.ai_girlfriend.models.llm import GenerationRequest, GenerationResponse


class FakeLLMProvider:
    """Configurable fake LLM provider."""

    provider = "fake"

    def __init__(
        self,
        response: str = "Hello!",
        chunks: list[str] | None = None,
        error: Exception | None = None,
        responder: Callable[[GenerationRequest], str] | None = None,
    ):
        self.response = response
        self.chunks = chunks
        self.error = error
        self.responder = responder
        self.requests: list[GenerationRequest] = []

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        content = self.responder(request) if self.responder else self.response
        return GenerationResponse(content=content, metadata={"provider": "fake"})

    async def stream(self, request: GenerationRequest) -> AsyncIterator[StreamEvent]:
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        if self.chunks is not None:
            pieces = self.chunks
        else:
            content = self.responder(request) if self.responder else self.response
            pieces = [content]
        for piece in pieces:
            yield TextDelta(text=piece)
        yield Done(usage={"total_tokens": 0}, metadata={"provider": "fake"})


__all__ = ["FakeLLMProvider"]
