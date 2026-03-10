from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from src.core.config import settings

class LLMFactory:
    @staticmethod
    def get_model(is_reasoning: bool = True):
        model_name = settings.REASONING_MODEL if is_reasoning else settings.ROUTING_MODEL

        if not settings.FIREWORKS_API_KEY:
            raise ValueError("Falta FIREWORKS_API_KEY en el .env")

        return ChatOpenAI(
            model=model_name,
            base_url="https://api.fireworks.ai/inference/v1",
            api_key=SecretStr(settings.FIREWORKS_API_KEY),
            temperature=0.7 if is_reasoning else 0.1,
            max_tokens=2048 if is_reasoning else 512
        )