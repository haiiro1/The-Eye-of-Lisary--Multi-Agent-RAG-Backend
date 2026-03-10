from src.core.factory import LLMFactory
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.core.logging_config import logger
import re

class DnDRouter:
    def __init__(self):
        self.llm = LLMFactory.get_model(is_reasoning=False)

    def classify_intent(self, user_input: str, messages: list = [], sheet_context: str = None) -> dict:
        # 1. (Opcional) Lógica de detección de idioma y condensación igual que antes

        # 2. Nueva Lógica de Prioridad Temporal:
        # Si detectamos que es una duda de reglas/hechizos, enviamos a WEB
        # hasta que arreglemos el RAG local.

        prompt = ChatPromptTemplate.from_template("""
            Eres el Orquestador de D&D 5e. Clasifica la intención:
            - 'WEB': Para cualquier duda sobre reglas, hechizos, monstruos o lore (Prioridad actual).
            - 'SHEET': Solo si pregunta específicamente por "mi" personaje o datos de su ficha.
            - 'CHAT': Saludos o charla informal.
            - 'BUILDER': Creación de personajes.

            Responde ÚNICAMENTE con la etiqueta.
            Entrada: {input}
        """)

        raw_decision = (prompt | self.llm | StrOutputParser()).invoke({"input": user_input}).strip().upper()

        # Forzamos la redirección a WEB para SPELLS y RULES por ahora
        if any(x in raw_decision for x in ["SPELLS", "RULES", "WEB"]):
            decision = "WEB"
        elif "SHEET" in raw_decision:
            decision = "SHEET"
        elif "BUILDER" in raw_decision:
            decision = "BUILDER"
        else:
            decision = "CHAT"

        return {
            "intent": decision,
            "language": "es", # o el detectado
            "contextualized_input": user_input
        }