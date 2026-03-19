from langchain_fireworks import ChatFireworks
from src.core.config import settings
from typing import Optional

# Tokens de parada específicos para modelos Qwen/Llama en Fireworks
STOP_TOKENS = ["<|im_end|>", "<|endoftext|>", "<|file_separator|>"]

class LLMFactory:
    @staticmethod
    def get_model(is_reasoning: bool = True, callbacks: Optional[list] = None):
        """
        Retorna una instancia configurada de ChatFireworks.
        Permite pasar callbacks externos (como el de Langfuse definido en main.py).
        """

        # Selección del modelo desde settings
        model_name = settings.REASONING_MODEL if is_reasoning else settings.ROUTING_MODEL

        if not settings.FIREWORKS_API_KEY:
            raise ValueError("Falta FIREWORKS_API_KEY en la configuración.")

        # Configuramos el modelo usando la librería nativa de Fireworks
        #se integra porque es mas eficiente que el wrapper genérico de OpenAI
        return ChatFireworks(
        model=model_name,
        fireworks_api_key=settings.FIREWORKS_API_KEY,
        temperature=0.7 if is_reasoning else 0.2, # Un poco más bajo para el agregador
        # Aumentamos a 1024 para que el agregador no se corte
        max_tokens=2048 if is_reasoning else 1024, 
        model_kwargs={
            "top_p": 0.9,
            "stop": STOP_TOKENS
        },
        callbacks=callbacks
    )