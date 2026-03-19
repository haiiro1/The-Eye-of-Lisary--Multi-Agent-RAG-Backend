import re
from src.core.factory import LLMFactory
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.core.logging_config import logger
from typing import Optional, List

class DnDRouter:
    def __init__(self, callbacks: Optional[List] = None):
        self.callbacks = callbacks
        self.llm = LLMFactory.get_model(is_reasoning=False, callbacks=self.callbacks)

    def classify_intent(self, user_input: str) -> dict:
        # Atajo para saludos y mensajes cortos: evita latencia y errores de clasificación
        saludos = ["hola", "buenas", "hi", "hey", "qué tal", "como estas", "saludos", "buen día", "buenas tardes", "buenas noches", "ola"]
        if len(user_input.split()) < 4 and any(s in user_input.lower() for s in saludos):
            logger.info("👋 Saludo detectado: saltando clasificación por IA")
            return {"intents": ["chat"]}

        logger.info(f"🔍 Clasificando intención: {user_input[:50]}...")

        prompt = ChatPromptTemplate.from_template("""
            [SISTEMA: MODO CLASIFICACIÓN ESTRICTO]
            Analiza la petición de D&D 5e y devuelve una lista de etiquetas.

            ETIQUETAS:
            - RULES: Mecánicas, combate, dotes.
            - SPELLS: Hechizos, magia.
            - BUILDER: Personajes, fichas.
            - WEB: Lore o datos de internet.
            - CHAT: Saludos o charla casual.

            REGLA: Responde SOLO con las etiquetas en mayúsculas separadas por comas.
            Entrada: {input}
            Respuesta:""")

        chain = prompt | self.llm | StrOutputParser()

        try:
            raw_response = chain.invoke(
                {"input": user_input},
                config={"callbacks": self.callbacks, "run_name": "Router_Intent_Classification"}
            )

            # Se limpia el texto por si el modelo incluye bloques de razonamiento <think>
            clean_text = re.sub(r'<think>.*?</think>', '', raw_response, flags=re.DOTALL)
            raw_upper = clean_text.upper().strip()

            # Extracción de etiquetas válidas mediante regex
            found_tags = re.findall(r'(RULES|SPELLS|BUILDER|WEB|CHAT)', raw_upper)
            final_intents = list(set([tag.lower() for tag in found_tags]))

            # Si no se detecta ninguna etiqueta, se redirige a chat por defecto
            if not final_intents:
                return {"intents": ["chat"]}

            return {"intents": final_intents}

        except Exception as e:
            logger.error(f"❌ Error en la clasificación del Router: {e}")
            return {"intents": ["chat"]}