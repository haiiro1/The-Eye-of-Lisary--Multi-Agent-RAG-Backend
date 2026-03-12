from src.core.factory import LLMFactory
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

class DnDRouter:
    def __init__(self):
        self.llm = LLMFactory.get_model(is_reasoning=False)

    def classify_intent(self, user_input: str) -> dict:
        prompt = ChatPromptTemplate.from_template("""
            Eres el Orquestador de D&D 5e. Clasifica las intenciones del usuario.
            Puedes elegir múltiples separadas por comas.
            Categorías:
            - 'WEB': Reglas, hechizos o lore (Prioridad actual).
            - 'BUILDER': Ficha de personaje o creación.
            - 'CHAT': Saludos.

            Responde ÚNICAMENTE con las etiquetas.
            Entrada: {input}
        """)

        raw = (prompt | self.llm | StrOutputParser()).invoke({"input": user_input}).upper()
        intents = [i.strip() for i in raw.split(",")]

        # Mapeo dinámico y limpieza
        final = []
        for i in intents:
            if i in ["SPELLS", "RULES", "WEB"]: final.append("WEB")
            elif "BUILDER" in i: final.append("BUILDER")
            else: final.append("CHAT")

        return {"intents": list(set(final)), "language": "es"}