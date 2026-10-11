"""AI controller and provider factory.

``AIController`` is the application-layer boundary over ``ILLMProvider``: it
adds timeouts and normalizes provider failures into the domain error hierarchy.
``LLMProviderFactory`` creates concrete providers only inside the composition
root (see spec, sections 2 and 7).
"""

from collections.abc import AsyncIterator

from src.ai_girlfriend.exc import GenerationTimeoutError, ProviderError
from src.ai_girlfriend.models.events import Error as ErrorEvent
from src.ai_girlfriend.models.events import StreamEvent
from src.ai_girlfriend.models.llm import (
    GenerationRequest,
    GenerationResponse,
    ILLMProvider,
)


class AIController:
    """Coordinates calls to an ``ILLMProvider`` with timeouts and error mapping."""

    def __init__(self, provider: ILLMProvider, request_timeout: float | None = None):
        self.provider = provider
        self.request_timeout = request_timeout

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate a full response, converting failures to domain errors."""
        try:
            if self.request_timeout is not None:
                import asyncio

                return await asyncio.wait_for(
                    self.provider.generate(request), timeout=self.request_timeout
                )
            return await self.provider.generate(request)
        except TimeoutError as exc:
            raise GenerationTimeoutError(
                f"Generation timed out after {self.request_timeout}s"
            ) from exc
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError(f"Provider generation failed: {exc}") from exc

    async def stream(self, request: GenerationRequest) -> AsyncIterator[StreamEvent]:
        """Stream a response, exposing domain ``Error`` events on failure."""
        try:
            async for event in self.provider.stream(request):
                yield event
        except TimeoutError as exc:
            yield ErrorEvent(
                message=f"Generation timed out after {self.request_timeout}s",
                code="timeout",
            )
            raise GenerationTimeoutError(
                f"Generation timed out after {self.request_timeout}s"
            ) from exc
        except ProviderError as exc:
            yield ErrorEvent(message=str(exc), code="provider_error")
            raise
        except Exception as exc:
            yield ErrorEvent(message=str(exc), code="provider_error")
            raise ProviderError(f"Provider streaming failed: {exc}") from exc


class LLMProviderFactory:
    """Creates ``ILLMProvider`` instances from settings (composition root only)."""

    @staticmethod
    def create_provider(
        provider_name: str,
        model: str,
        url: str | None = None,
        api_key: str | None = None,
    ) -> ILLMProvider:
        """Instantiate a concrete provider by its configured name."""
        if provider_name == "ollama":
            from src.ai_girlfriend.llm.ollama_provider import OllamaProvider

            return OllamaProvider(model=model, url=url or "http://localhost:11434")
        if provider_name == "deepseek":
            from src.ai_girlfriend.llm.deepseek_provider import DeepSeekProvider

            if api_key is None:
                raise ProviderError("DeepSeek provider requires an API key")
            return DeepSeekProvider(model=model, api_key=api_key)
        raise ProviderError(f"Unsupported LLM provider: {provider_name}")


__all__ = ["AIController", "LLMProviderFactory"]
