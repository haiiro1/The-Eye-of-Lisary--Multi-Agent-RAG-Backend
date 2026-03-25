from typing import Dict, Any, Optional
from src.core.base_agent import BaseDnDAgent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableConfig
from src.core.callbacks import get_langfuse_client
from src.core.logging_config import logger
from src.core.factory import LLMFactory

class ChatExpert(BaseDnDAgent):
    def __init__(self, session_id, chat_history=None, callbacks=None):
        super().__init__(session_id, chat_history, callbacks)
        # Forzamos modelo ligero para respuestas rápidas y económicas
        self.llm = LLMFactory.get_model(is_reasoning=False, callbacks=self.callbacks)

    def _setup_tools(self):
        return {}

    def run(self, user_input: str, language: str = "es", extra_info: str = "", config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
        logger.info(f"💬 [ChatExpert] Respondiendo a interacción social...")

        client = get_langfuse_client()
        prompt_res = client.get_prompt("dnd-chat-expert")

        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_res.get_langchain_prompt()),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}")
        ])

        chain = prompt | self.llm | StrOutputParser()

        answer = chain.invoke({
            "question": user_input,
            "lang": language,
            "chat_history": self.memory_messages
        }, config=config)

        return {"agent": "ChatExpert", "answer": answer}