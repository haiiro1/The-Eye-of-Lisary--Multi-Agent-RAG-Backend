from abc import ABC, abstractmethod
from src.core.factory import LLMFactory
from src.core.memory import get_chat_history
from typing import Any, Optional

class BaseDnDAgent(ABC):
    def __init__(self, session_id: str):
        self.session_id = session_id
        # Los especialistas usan el modelo de razonamiento por defecto
        self.llm = LLMFactory.get_model(is_reasoning=True)
        self.memory = get_chat_history(session_id)
        self.tools = self._setup_tools()

    @abstractmethod
    def _setup_tools(self) -> Any:
        """Define las herramientas (RAG, Wiki, etc.) que usará el agente."""
        pass

    @abstractmethod
    def run(self, user_input: str, language: str = "es") -> dict:
        """Ejecuta la lógica principal del agente. Devuelve un dict con la respuesta."""
        pass