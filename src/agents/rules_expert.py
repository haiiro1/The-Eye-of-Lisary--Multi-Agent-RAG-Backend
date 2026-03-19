from src.core.base_agent import BaseDnDAgent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableConfig # <--- Importante
from src.core.logging_config import logger
from typing import Optional

class RulesExpert(BaseDnDAgent):
    def _setup_tools(self):
        # El orquestador suministra la información de manuales (RAG)
        return {}

    def run(self, user_input: str, language: str = "es", extra_info: str = "", config: Optional[RunnableConfig] = None) -> dict:
        """
        Ejecuta el análisis de reglas.
        Ahora acepta 'config' para que Langfuse registre la generación del LLM.
        """
        logger.info(f"⚖️ [RulesExpert] Analizando mecánicas y reglas...")

        prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres el 'Custodio de las Leyes', el experto supremo en las reglas de D&D 5e.

            TU MISIÓN:
            Interpretar las reglas de forma precisa, clara y técnica.

            DIRECTRICES:
            1. PRIORIDAD: Usa los datos de manuales proporcionados por el orquestador.
            2. CLARIDAD: Explica no solo el 'qué', sino el 'cómo' se aplica la regla (ej. tipos de tiradas, modificadores).
            3. IMPARCIALIDAD: Eres un árbitro. Si una regla queda a discreción del DM (Dungeon Master), menciónalo.
            4. IDIOMA: Responde en {lang}.
            """),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", """CONTEXTO TÉCNICO DE MANUALES:
            {extra_info}

            CONSULTA SOBRE REGLAS:
            {question}""")
        ])

        # Construimos la cadena
        chain = prompt | self.llm | StrOutputParser()

        # Al pasar 'config' al invoke, LangChain busca automáticamente
        # los callbacks de Langfuse que inyectamos en main.py
        answer = chain.invoke({
            "extra_info": extra_info,
            "question": user_input,
            "lang": language,
            "chat_history": self.memory_messages
        }, config=config)

        return {"agent": "RulesExpert", "answer": answer}