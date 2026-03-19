from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from src.core.base_agent import BaseDnDAgent
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableConfig # Importante para trazabilidad
from src.core.logging_config import logger
from typing import Optional

class CharBuilder(BaseDnDAgent):
    def _setup_tools(self):
        return {} # Las herramientas las gestiona el orquestador/nodo

    def run(self, user_input: str, language: str = "es", extra_info: str = "", config: Optional[RunnableConfig] = None) -> dict:
        """
        Ejecuta el análisis de construcción y progresión de personajes.
        Acepta 'config' para propagar los callbacks de Langfuse hacia el LLM.
        """
        logger.info(f"🏗️ [CharBuilder] Analizando optimización y progresión...")

        prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres el 'Arquitecto de Almas', experto en optimización mecánica y narrativa de D&D 5e.

            TU MISIÓN:
            Analizar la solicitud del usuario comparándola con su ficha actual y las reglas oficiales.

            CAPACIDADES ESPECIALES:
            1. AUDITORÍA: Si detectas inconsistencias en la ficha (ej. bonificadores mal calculados), señálalo cortésmente.
            2. OPTIMIZACIÓN: Sugiere dotes, dotes de linaje o distribuciones de conjuros que maximicen el potencial del personaje.
            3. SUBIDA DE NIVEL: Si el usuario menciona subir de nivel, detalla EXACTAMENTE qué cambia:
               - Incremento de Vida (HP).
               - Nuevos espacios de conjuro y cantidad de conjuros a aprender.
               - Rasgos de clase nuevos.

            PROTOCOLO DE COLABORACIÓN:
            - Si el usuario es un lanzador de conjuros, menciona que invocarás al 'Mentor de Hechizos' (SpellMentor) para las recomendaciones específicas de magia.

            IDIOMA: Responde siempre en {lang}.
            """),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", """DATOS DE REFERENCIA (MANUALES Y FICHA):
            {extra_info}

            SOLICITUD DEL AVENTURERO:
            {question}""")
        ])

        # Definición de la cadena
        chain = prompt | self.llm | StrOutputParser()

        # --- PROPAGACIÓN DEL CONFIG ---
        # Pasamos el config para que Langfuse capture el intercambio de tokens
        # y el tiempo de respuesta de este agente específico.
        answer = chain.invoke({
            "extra_info": extra_info,
            "question": user_input,
            "lang": language,
            "chat_history": self.memory_messages
        }, config=config)

        return {"agent": "CharBuilder", "answer": answer}