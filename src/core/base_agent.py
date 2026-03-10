from abc import ABC, abstractmethod
from src.core.factory import LLMFactory
from src.core.memory import get_chat_history
from typing import Any, Optional, List

class BaseDnDAgent(ABC):
    def __init__(self, session_id: str, chat_history: Optional[List] = None):
        self.session_id = session_id
        # El modelo de razonamiento sigue siendo el estándar para expertos
        self.llm = LLMFactory.get_model(is_reasoning=True)

        # Si LangGraph nos pasa el historial del estado, lo usamos.
        # Si no, recurrimos a la persistencia clásica de SQL.
        if chat_history is not None:
            self.memory_messages = chat_history
        else:
            self.memory = get_chat_history(session_id)
            self.memory_messages = self.memory.messages

        self.tools = self._setup_tools()

    @abstractmethod
    def _setup_tools(self) -> Any:
        """Define las herramientas (RAG, Wiki, etc.) que usará el agente."""
        pass

    @abstractmethod
    def run(self, user_input: str, language: str = "es", extra_info: str = "") -> dict:
        """
        Ejecuta la lógica principal del agente.
        Añadimos 'extra_info' para recibir contexto de otros nodos del grafo.
        """
        pass