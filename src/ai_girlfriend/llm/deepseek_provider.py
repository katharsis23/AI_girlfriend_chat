import httpx
import asyncio
import json


class DeepSeekProvider:
    provider = "deepseek"

    def __init__(self, model: str, api_key: str, streaming: bool = False):
        self.model = model
        self.api_key = api_key
        self.streaming = streaming

    async def generate_response(self, request: str) -> dict[str, any]:
        """
        Generate a response from the DeepSeek LLM based on the given prompt.

        Args:
            request (str): The input request for the LLM.
        """
        # Implement the logic to generate a response using DeepSeek API
        yield

    async def stream_response(self, request: str) -> asyncio.AsyncIterator[dict[str, any]]:
        """
        Stream a response from the DeepSeek LLM based on the given prompt.

        Args:
            request (str): The input request for the LLM.
        """
        # Implement the logic to stream a response using DeepSeek API
        yield