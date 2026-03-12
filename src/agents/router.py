from src.core.factory import LLMFactory
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.core.logging_config import logger
import re

class DnDRouter:
    def __init__(self):
        self.llm = LLMFactory.get_model(is_reasoning=False)

    def classify_intent(self, user_input: str, messages: list = [], sheet_context: str = None) -> dict:
        prompt = ChatPromptTemplate.from_template("""
            Eres el Orquestador de D&D 5e. Clasifica las intenciones del usuario.
            Puedes elegir múltiples si es necesario, separadas por comas.

            Categorías:
            - 'WEB': Reglas generales, hechizos, lore o monstruos.
            - 'SHEET': Datos de la ficha del jugador o "mi" personaje.
            - 'BUILDER': Creación/modificación de personajes.
            - 'CHAT': Saludos o charla.

            Entrada: {input}
            Responde ÚNICAMENTE con las etiquetas separadas por comas (ejemplo: WEB, SHEET).
        """)

        raw_response = (prompt | self.llm | StrOutputParser()).invoke({"input": user_input}).strip().upper()

        # Parsear múltiples intenciones
        intents = [i.strip() for i in raw_response.split(",")]

        # Lógica de limpieza (manteniendo la redirección temporal a WEB)
        final_intents = []
        for i in intents:
            if i in ["SPELLS", "RULES", "WEB"]: final_intents.append("WEB")
            elif "SHEET" in i: final_intents.append("SHEET")
            elif "BUILDER" in i: final_intents.append("BUILDER")
            else: final_intents.append("CHAT")

        return {
            "intents": list(set(final_intents)), # Evitar duplicados
            "language": "es",
            "contextualized_input": user_input
        }