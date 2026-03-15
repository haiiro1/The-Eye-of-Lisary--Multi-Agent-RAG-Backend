# src/agents/router.py
from src.core.factory import LLMFactory
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.core.logging_config import logger

class DnDRouter:
    def __init__(self):
        # Usamos un modelo rápido para la clasificación
        self.llm = LLMFactory.get_model(is_reasoning=False)

    def classify_intent(self, user_input: str) -> dict:
        logger.info(f"🔍 [Router] Clasificando intención: {user_input[:50]}...")

        prompt = ChatPromptTemplate.from_template("""
            Eres el Orquestador Arcano de D&D 5e. Tu trabajo es analizar la petición del aventurero
            y decidir qué especialistas deben intervenir.

            ESPECIALISTAS DISPONIBLES:
            - 'BUILDER': Creación de personajes, optimización, subir de nivel, cambios en la ficha.
            - 'SPELLS': Consulta de hechizos, recomendaciones mágicas, aprendizaje de conjuros.
            - 'RULES': Mecánicas de combate, condiciones, dotes, reglas de ambiente.
            - 'WEB': Lore del mundo, datos de wikis, o si no encaja en las anteriores.
            - 'CHAT': Saludos o charlas irrelevantes para el juego.

            REGLA MULTI-AGENTE:
            Si el usuario sube de nivel o pide algo complejo, selecciona VARIOS.
            Ejemplo: "Subí a nivel 2 de Mago" -> BUILDER, SPELLS.
            Ejemplo: "¿Cómo funciona el ataque de oportunidad de este nuevo dote?" -> RULES, BUILDER.

            Responde ÚNICAMENTE con las etiquetas separadas por comas.
            Entrada: {input}
        """)

        # Invocación y limpieza
        raw = (prompt | self.llm | StrOutputParser()).invoke({"input": user_input}).upper()
        intents = [i.strip() for i in raw.split(",")]

        # Mapeo y validación de etiquetas contra los nodos del grafo
        final_intents = []
        valid_nodes = ["BUILDER", "SPELLS", "RULES", "WEB"]

        for i in intents:
            if i in valid_nodes:
                final_intents.append(i.lower())
            elif i == "CHAT":
                continue # El orquestador enviará al aggregator por defecto si no hay agentes

        # Eliminamos duplicados
        return {"intents": list(set(final_intents))}