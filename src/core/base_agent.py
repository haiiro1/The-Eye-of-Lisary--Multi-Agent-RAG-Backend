from abc import ABC, abstractmethod
from src.core.factory import LLMFactory
from src.core.memory import get_chat_history
from typing import Any, Optional, List, Dict

class BaseDnDAgent(ABC):
    def __init__(self, session_id: str, chat_history: Optional[List] = None):
        self.session_id = session_id
        # Mantenemos el modelo de razonamiento para la lógica de los expertos
        self.llm = LLMFactory.get_model(is_reasoning=True)

        # AJUSTE: Priorizar siempre el historial del grafo para mantener el estado
        if chat_history is not None:
            self.memory_messages = chat_history
        else:
            # Respaldo en la base de datos si no hay historial previo en el grafo
            self.memory = get_chat_history(session_id)
            self.memory_messages = self.memory.messages

        self.tools = self._setup_tools()

    @abstractmethod
    def _setup_tools(self) -> Any:
        """Define las herramientas (RAG, Wiki, etc.) que usará el agente."""
        pass

    @abstractmethod
    def run(self, user_input: str, language: str = "es", extra_info: str = "") -> Dict[str, Any]:
        """
        Ejecuta la lógica principal.
        DEBE devolver un diccionario con la clave 'answer' para ser compatible con nodes.py.
        """
        pass