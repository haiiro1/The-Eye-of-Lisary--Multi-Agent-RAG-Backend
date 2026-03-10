from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from src.core.config import settings

# Definimos los tokens de parada como una constante para mayor mantenibilidad
# según la recomendación del Code Review
STOP_TOKENS = ["<|im_end|>", "<|endoftext|>"]

class LLMFactory:
    @staticmethod
    def get_model(is_reasoning: bool = True):
        # Selección dinámica del modelo basado en la configuración
        model_name = settings.REASONING_MODEL if is_reasoning else settings.ROUTING_MODEL

        if not settings.FIREWORKS_API_KEY:
            raise ValueError("Falta FIREWORKS_API_KEY en el archivo .env")

        return ChatOpenAI(
            model=model_name,
            base_url="https://api.fireworks.ai/inference/v1",
            api_key=SecretStr(settings.FIREWORKS_API_KEY),
            # Temperatura baja (0.1) para el Router y alta (0.7) para Expertos
            temperature=0.7 if is_reasoning else 0.1,
            max_tokens=2048 if is_reasoning else 512,
            model_kwargs={
                "top_p": 0.9,
                "stop": STOP_TOKENS  # Aplicamos la constante aquí
            }
        )