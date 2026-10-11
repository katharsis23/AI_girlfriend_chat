from src.ai_girlfriend.models.llm import ILLMProvider

class AIController:
    def __init__(self, llm_provider: ILLMProvider):
        self.llm_provider = llm_provider

    def generate_response(self, request):
        # Use the LLM provider to generate a response based on user input
        response = self.llm_provider.generate(request)
        return response

    def stream_response(self, request):
        # Use the LLM provider to stream a response based on user input
        for chunk in self.llm_provider.stream(request):
            yield chunk


class LLMProviderFactory:
    @staticmethod
    def create_provider(provider_name: str, model: str, api_key: str | None = None, streaming: bool = False) -> ILLMProvider:
        if provider_name == "ollama":
            from src.ai_girlfriend.llm.ollama_provider import OllamaProvider
            return OllamaProvider(model=model, api_key=api_key, streaming=streaming)
        elif provider_name == "deepseek":
            from src.ai_girlfriend.llm.deepseek_provider import DeepSeekProvider
            return DeepSeekProvider(model=model, api_key=api_key, streaming=streaming)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider_name}")