from abc import ABC, abstractmethod
from src.core.factory import LLMFactory
from src.core.memory import get_chat_history
from typing import Any, Optional, List, Dict

class BaseDnDAgent(ABC):
    def __init__(
        self, 
        session_id: str, 
        chat_history: Optional[List] = None, 
        callbacks: Optional[List] = None # <-- Nuevo: Recibe los callbacks de Langfuse
    ):
        self.session_id = session_id
        self.callbacks = callbacks # Almacenamos para posibles herramientas (tools)

        # Configuramos el LLM inyectando los callbacks para monitoreo total
        self.llm = LLMFactory.get_model(
            is_reasoning=True, 
            callbacks=self.callbacks
        )

        # Gestión de memoria del agente
        if chat_history is not None:
            self.memory_messages = chat_history
        else:
            # Respaldo en BD (usado si el agente se llama fuera del flujo de LangGraph)
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
        DEBE devolver un diccionario con la clave 'answer'.
        """
        pass