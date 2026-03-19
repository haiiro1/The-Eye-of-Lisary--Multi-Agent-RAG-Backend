import re
from src.core.factory import LLMFactory
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.core.logging_config import logger
from typing import Optional, List

class DnDRouter:
    def __init__(self, callbacks: Optional[List] = None):
        self.callbacks = callbacks
        # Forzamos un modelo NO de razonamiento para clasificación si es posible, 
        # o un prompt mucho más agresivo.
        self.llm = LLMFactory.get_model(is_reasoning=False, callbacks=self.callbacks)

    def classify_intent(self, user_input: str) -> dict:
        logger.info(f"🔍 [Router] Clasificando intención: {user_input[:50]}...")

        # Prompt optimizado para evitar explicaciones
        prompt = ChatPromptTemplate.from_template("""
            [SISTEMA: MODO CLASIFICACIÓN ESTRICTO]
            Analiza la petición de D&D 5e y devuelve una lista de etiquetas.

            ETIQUETAS:
            - RULES: Mecánicas, combate, dotes, Action Surge, ataques.
            - SPELLS: Hechizos, conjuros, magia.
            - BUILDER: Personajes, niveles, ficha, clases.
            - WEB: Lore, wikis, datos externos.
            - CHAT: Saludos o charlas breves.

            REGLA: Responde SOLO con las etiquetas en mayúsculas separadas por comas.
            Sin explicaciones, sin etiquetas de formato, sin introducciones.

            Entrada: {input}
            Respuesta:""")

        chain = prompt | self.llm | StrOutputParser()

        try:
            raw_response = chain.invoke(
                {"input": user_input},
                config={"callbacks": self.callbacks, "run_name": "Router_Intent_Classification"}
            )

            # --- LIMPIEZA ANTIBALAS ---
            # 1. Eliminamos bloques <think> si el modelo los añade
            clean_text = re.sub(r'<think>.*?</think>', '', raw_response, flags=re.DOTALL)

            # 2. Pasamos a mayúsculas y limpiamos espacios
            raw_upper = clean_text.upper().strip()

            # 3. Extraemos solo las palabras válidas usando regex para ignorar puntos, frases o basura
            found_tags = re.findall(r'(RULES|SPELLS|BUILDER|WEB|CHAT)', raw_upper)

            # Mapeo final
            final_intents = []
            for tag in found_tags:
                if tag != "CHAT":
                    final_intents.append(tag.lower())

            # Eliminamos duplicados
            final_intents = list(set(final_intents))

            logger.info(f"✅ [Router] Intenciones finales: {final_intents}")
            return {"intents": final_intents}

        except Exception as e:
            logger.error(f"❌ Error en la clasificación del Router: {e}")
            return {"intents": []}