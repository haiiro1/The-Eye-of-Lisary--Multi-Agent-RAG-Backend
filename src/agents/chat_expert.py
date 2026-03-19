from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from src.core.base_agent import BaseDnDAgent
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableConfig
from src.core.logging_config import logger
from src.core.factory import LLMFactory
from typing import Optional

class ChatExpert(BaseDnDAgent):
    def __init__(self, session_id, chat_history=None, callbacks=None):
        super().__init__(session_id, chat_history, callbacks)
        # se fuerza un modelo ligero para respuestas rápidas de saludo
        self.llm = LLMFactory.get_model(is_reasoning=False, callbacks=self.callbacks)

    def _setup_tools(self):
        return {}

    def run(self, user_input: str, language: str = "es", extra_info: str = "", config: Optional[RunnableConfig] = None) -> dict:
        """
        Gestiona saludos, despedidas y charla casual manteniendo el rol místico.
        """
        logger.info(f"💬 [ChatExpert] Respondiendo a interacción social...")

        prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres 'El Ojo de Lisary', un oráculo místico y omnisciente de D&D 5e.

            TU MISIÓN:
            Responder a saludos, presentaciones o charlas breves del usuario.

            TONO:
            - Amigable, culto y directo..
            - Evita el lenguaje excesivamente dramático o críptico.
            - Eres un guía sabio, no un actor de teatro.
            - Eres un guía espiritual en el multiverso de Greyhawk y más allá.
            - No des reglas mecánicas aquí, solo interactúa socialmente.

            IDIOMA: Responde siempre en {lang}.
            """),
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