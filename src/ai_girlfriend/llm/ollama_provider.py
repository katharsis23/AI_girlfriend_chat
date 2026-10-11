import httpx
import asyncio

class OllamaProvider:
    provider = "ollama"

    def __init__(self, model: str, api_key: str | None = None, streaming: bool = False):
        self.model = model
        self.api_key = api_key
        self.streaming = streaming

    async def generate_response(self, request: str) -> dict[str, any]:
       ...

    async def stream_response(self, request: str) -> asyncio.AsyncIterator[dict[str, any]]:
        ...