from src.core.base_agent import BaseDnDAgent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableConfig # Fundamental para el rastro
from src.core.logging_config import logger
from typing import Optional

class WebOmniExpert(BaseDnDAgent):
    def _setup_tools(self):
        # El orquestador suministra la información de la Web/Wiki
        return {}

    def run(self, user_input: str, language: str = "es", extra_info: str = "", config: Optional[RunnableConfig] = None) -> dict:
        """
        Ejecuta la síntesis de conocimiento externo.
        Acepta 'config' para propagar los callbacks de Langfuse.
        """
        logger.info(f"🌐 [WebOmniExpert] Consultando conocimiento externo...")

        prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres el 'Omnisciente del Velo', un experto en D&D 5e con acceso a bibliotecas infinitas.

            TU MISIÓN:
            Sintetizar información de fuentes externas (Wikis, foros especializados y documentos online) para responder al aventurero.

            DIRECTRICES:
            1. FILTRADO: Usa los datos externos proporcionados para dar una respuesta veraz.
            2. CONTEXTO: Si la información proviene de una Wiki, trata de mantener el tono oficial de D&D 5e.
            3. LIMITACIÓN: Si no hay datos claros en la información proporcionada, usa tu conocimiento base pero advierte que es conocimiento general.
            4. IDIOMA: Responde en {lang}.
            """),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", """INFORMACIÓN RECUPERADA DEL EXTERIOR:
            {extra_info}

            CONSULTA DEL AVENTURERO:
            {question}""")
        ])

        # Construcción de la cadena uniendo prompt, modelo y parser
        chain = prompt | self.llm | StrOutputParser()

        # --- PROPAGACIÓN DEL CONFIG ---
        # Al pasar el config, permitimos que LangChain envíe la telemetría
        # del LLM (tokens, tiempo, coste) directamente a Langfuse.
        answer = chain.invoke({
            "extra_info": extra_info,
            "question": user_input,
            "lang": language,
            "chat_history": self.memory_messages
        }, config=config)

        return {"agent": "WebOmniExpert", "answer": answer}