"""OpenAI-compatible provider (used for the DeepSeek API).

Talks to the ``/chat/completions`` endpoint over ``httpx``, supporting both
one-shot and streaming (SSE) responses. Client errors are translated into the
domain error hierarchy (see spec, section 6.1).
"""

import json
from collections.abc import AsyncIterator

import httpx

from src.ai_girlfriend.exc import GenerationTimeoutError, ProviderError
from src.ai_girlfriend.models.events import Done, Error, StreamEvent, TextDelta
from src.ai_girlfriend.models.llm import GenerationRequest, GenerationResponse

_STREAM_TIMEOUT = httpx.Timeout(connect=10.0, read=120.0, write=30.0, pool=10.0)


class DeepSeekProvider:
    """``ILLMProvider`` implementation for OpenAI-compatible HTTP APIs."""

    provider = "deepseek"

    def __init__(
        self,
        model: str,
        api_key: str,
        url: str = "https://api.deepseek.com/v1",
        timeout: float | None = None,
    ):
        self.model = model
        self.api_key = api_key
        self.url = url.rstrip("/")
        self.timeout = timeout

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

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
                    f"{self.url}/chat/completions",
                    headers=self._headers,
                    json=self._payload(request, stream=False),
                )
                response.raise_for_status()
                data = response.json()
        except httpx.TimeoutException as exc:
            raise GenerationTimeoutError("DeepSeek request timed out") from exc
        except httpx.HTTPError as exc:
            raise ProviderError(f"DeepSeek request failed: {exc}") from exc

        content = data["choices"][0]["message"]["content"]
        raw_usage = data.get("usage", {})
        usage = {
            "prompt_tokens": raw_usage.get("prompt_tokens", 0),
            "completion_tokens": raw_usage.get("completion_tokens", 0),
        }
        return GenerationResponse(
            content=content,
            usage=usage,
            metadata={"model": data.get("model", self.model)},
        )

    async def stream(self, request: GenerationRequest) -> AsyncIterator[StreamEvent]:
        """Stream the response as ``TextDelta`` events ending in ``Done``."""
        payload = self._payload(request, stream=True)
        model_name = request.model or self.model
        try:
            async with httpx.AsyncClient(timeout=_STREAM_TIMEOUT) as client:
                async with client.stream(
                    "POST",
                    f"{self.url}/chat/completions",
                    headers=self._headers,
                    json=payload,
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line.startswith("data:"):
                            continue
                        data = line[len("data:") :].strip()
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                        except json.JSONDecodeError:
                            continue
                        delta = chunk["choices"][0].get("delta", {})
                        text = delta.get("content", "")
                        if text:
                            yield TextDelta(text=text)
                        model_name = chunk.get("model", model_name)
        except httpx.TimeoutException as exc:
            yield Error(message="DeepSeek stream timed out", code="timeout")
            raise GenerationTimeoutError("DeepSeek stream timed out") from exc
        except httpx.HTTPError as exc:
            yield Error(message=f"DeepSeek stream failed: {exc}", code="provider_error")
            raise ProviderError(f"DeepSeek stream failed: {exc}") from exc

        yield Done(usage={}, metadata={"model": model_name})


__all__ = ["DeepSeekProvider"]
