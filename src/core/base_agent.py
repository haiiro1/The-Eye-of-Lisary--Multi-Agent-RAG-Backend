from abc import ABC, abstractmethod
from src.core.factory import LLMFactory
from src.core.memory import get_chat_history
from typing import Any

class BaseDnDAgent(ABC):
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.llm = LLMFactory.get_model(is_reasoning=True)
        self.memory = get_chat_history(session_id)
        self.tools = self._setup_tools()

    @abstractmethod
    def _setup_tools(self) -> Any:
        pass

    @abstractmethod
    def run(self, user_input: str):
        pass

    @abstractmethod
    def run(self, user_input: str, language: str = "es"):
        pass