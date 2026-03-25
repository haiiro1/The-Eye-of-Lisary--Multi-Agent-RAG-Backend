from langchain_fireworks import ChatFireworks
from src.core.config import settings
from typing import Optional

# Tokens de parada específicos para modelos Qwen/Llama en Fireworks
STOP_TOKENS = ["<|im_end|>", "<|endoftext|>", "<|file_separator|>"]

class LLMFactory:
    @staticmethod
    def get_model(is_reasoning: bool = True, callbacks: Optional[list] = None):
        """
        Retorna una instancia configurada de ChatFireworks eliminando Warnings de parámetros.
        """
        model_name = settings.REASONING_MODEL if is_reasoning else settings.ROUTING_MODEL

        if not settings.FIREWORKS_API_KEY:
            raise ValueError("Falta FIREWORKS_API_KEY en la configuración.")

        return ChatFireworks(
            model=model_name,
            fireworks_api_key=settings.FIREWORKS_API_KEY,
            temperature=0.7 if is_reasoning else 0.2,
            max_tokens=2048 if is_reasoning else 1024,
            # Argumento directo para evitar el warning de 'stop'
            stop=STOP_TOKENS,
            # model_kwargs para parámetros específicos del proveedor
            model_kwargs={
                "top_p": 0.9
            },
            callbacks=callbacks
        )