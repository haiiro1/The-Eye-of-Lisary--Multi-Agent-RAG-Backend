from src.core.base_agent import BaseDnDAgent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from src.core.logging_config import logger

class SpellMentor(BaseDnDAgent):
    def _setup_tools(self):
        # El orquestador suministra la información de hechizos (RAG)
        return {}

    def run(self, user_input: str, language: str = "es", extra_info: str = "") -> dict:
        logger.info(f"🔮 [SpellMentor] Analizando el tejido arcano...")

        prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres el 'Mentor de Hechizos', un archimago experto en la teoría y práctica de la magia en D&D 5e.

            TU MISIÓN:
            Guiar al aventurero en la selección y uso de sus dotes mágicas y conjuros.

            CAPACIDADES ESTRATÉGICAS:
            1. RECOMENDACIÓN: Sugiere hechizos basados en el nivel y clase del usuario, priorizando la utilidad y el poder.
            2. SINERGIA: Explica cómo combinar hechizos (ej. "Grasa" + "Crecimiento de Espinas").
            3. ACLARACIÓN: Explica componentes (V, S, M), tiempos de lanzamiento, concentración de forma sencilla, daño, áreas de efecto, etc.

            CONEXIÓN CON EL ARQUITECTO (CharBuilder):
            Si el usuario está subiendo de nivel, enfócate en llenar los 'huecos' que el Arquitecto de Almas ha identificado.

            IDIOMA: Responde en {lang}.
            """),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", """CONJUROS DISPONIBLES Y REGLAS (RAG):
            {extra_info}

            CONSULTA MÁGICA:
            {question}""")
        ])

        chain = prompt | self.llm | StrOutputParser()

        # Usamos self.memory_messages inyectado por LangGraph
        answer = chain.invoke({
            "extra_info": extra_info,
            "question": user_input,
            "lang": language,
            "chat_history": self.memory_messages
        })

        return {"agent": "SpellMentor", "answer": answer}