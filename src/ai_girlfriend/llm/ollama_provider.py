"""Ollama provider implemented on top of the HTTP ``/api/chat`` endpoint.

Uses ``httpx`` directly (no ``ollama`` SDK). Streaming follows the newline
delimited JSON (NDJSON) protocol Ollama emits. All client errors are translated
into the domain error hierarchy (see spec, section 6.1).
"""

import json
from collections.abc import AsyncIterator

import httpx

from src.ai_girlfriend.exc import GenerationTimeoutError, ProviderError
from src.ai_girlfriend.models.events import Done, Error, StreamEvent, TextDelta
from src.ai_girlfriend.models.llm import GenerationRequest, GenerationResponse

_STREAM_TIMEOUT = httpx.Timeout(connect=10.0, read=120.0, write=30.0, pool=10.0)


class OllamaProvider:
    """``ILLMProvider`` implementation talking to a local Ollama server."""

    provider = "ollama"

    def __init__(
        self,
        model: str,
        url: str = "http://localhost:11434",
        timeout: float | None = None,
    ):
        self.model = model
        self.url = url.rstrip("/")
        # `None` keeps the streaming-friendly default; a number caps total time.
        self.timeout = timeout

    def _payload(self, request: GenerationRequest, *, stream: bool) -> dict:
        messages = [
            {"role": message.role.value, "content": message.content}
            for message in request.messages
        ]
        payload: dict = {
            "model": request.model or self.model,
            "messages": messages,
            "stream": stream,
        }
        payload.update(request.params)
        return payload

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Request a single, complete response."""
        timeout = self.timeout if self.timeout is not None else _STREAM_TIMEOUT
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{self.url}/api/chat",
                    json=self._payload(request, stream=False),
                )
                response.raise_for_status()
                data = response.json()
        except httpx.TimeoutException as exc:
            raise GenerationTimeoutError("Ollama request timed out") from exc
        except httpx.HTTPError as exc:
            raise ProviderError(f"Ollama request failed: {exc}") from exc

        content = data.get("message", {}).get("content", "")
        usage = {
            "prompt_tokens": data.get("prompt_eval_count", 0),
            "completion_tokens": data.get("eval_count", 0),
        }
        return GenerationResponse(
            content=content,
            usage=usage,
            metadata={"model": data.get("model", self.model)},
        )

    async def stream(self, request: GenerationRequest) -> AsyncIterator[StreamEvent]:
        """Stream the response as discrete ``TextDelta`` events ending in ``Done``."""
        payload = self._payload(request, stream=True)
        usage: dict[str, int] = {}
        model_name = request.model or self.model
        try:
            async with httpx.AsyncClient(timeout=_STREAM_TIMEOUT) as client:
                async with client.stream(
                    "POST", f"{self.url}/api/chat", json=payload
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        try:
                            chunk = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        text = chunk.get("message", {}).get("content", "")
                        if text:
                            yield TextDelta(text=text)
                        if chunk.get("done"):
                            usage = {
                                "prompt_tokens": chunk.get("prompt_eval_count", 0),
                                "completion_tokens": chunk.get("eval_count", 0),
                            }
                            model_name = chunk.get("model", model_name)
        except httpx.TimeoutException as exc:
            yield Error(message="Ollama stream timed out", code="timeout")
            raise GenerationTimeoutError("Ollama stream timed out") from exc
        except httpx.HTTPError as exc:
            yield Error(message=f"Ollama stream failed: {exc}", code="provider_error")
            raise ProviderError(f"Ollama stream failed: {exc}") from exc

        yield Done(usage=usage, metadata={"model": model_name})


__all__ = ["OllamaProvider"]
