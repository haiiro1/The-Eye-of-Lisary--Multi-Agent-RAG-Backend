from src.core.base_agent import BaseDnDAgent
from src.tools.rag_tool import RAGTool
from src.tools.ConditionExpertTool import ConditionExpertTool
from src.tools.CombatCalculatorTool import CombatCalculatorTool
# ELIMINADO: Ya no importa ni instancia WebOmniExpert directamente
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from src.core.logging_config import logger

class SpellMentor(BaseDnDAgent):
    def _setup_tools(self):
        # El mentor ahora se centra exclusivamente en el conocimiento de manuales locales
        return {
            "rag": RAGTool(k=3),
            "conditions": ConditionExpertTool(),
            "calculator": CombatCalculatorTool()
        }

    def run(self, user_input: str, language: str = "es", extra_info: str = "") -> dict:
        logger.info(f"🧙‍♂️ [SpellMentor] Analizando conocimientos arcanos en modo nodo...")

        # 1. Buscamos en los manuales locales (RAG)
        context = self.tools["rag"].search(user_input)

        # 2. Prompt Maestro Arcano
        # El parámetro extra_info permite recibir conocimiento web procesado previamente por el grafo
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres el Mentor de Hechizos del Ojo de Lisary, una autoridad absoluta en artes arcanas y divinas.
            Tu misión es explicar la magia de D&D 5e con máxima precisión técnica.

            PROTOCOLOS DE ENSEÑANZA:
            1. VERACIDAD RAG: Tus respuestas deben basarse ESTRICTAMENTE en el 'CONOCIMIENTO LOCAL (RAG)'. Si un dato (como Componentes M) no aparece en el RAG, di "No especificado en mis archivos" en lugar de inventarlo.
            2. FICHA TÉCNICA: Indica siempre Nivel, Tiempo de lanzamiento, Alcance (y área de efecto exacta), Componentes y Duración.
            3. ÁREA DE EFECTO: Sé extremadamente preciso. Diferencia entre Esfera, Cono, Línea o Cilindro según el manual.
            4. CONCENTRACIÓN: Si el hechizo la requiere, márcalo en negrita al inicio.
            5. IDIOMA: Responde en {lang}. Usa el nombre en inglés entre paréntesis si es distinto.
            6. ESTRATEGIA: Sugiere usos tácticos basados en las reglas, pero nunca inventes mecánicas o bonos numéricos que no existan en el sistema D&D 5e."""),

            MessagesPlaceholder(variable_name="chat_history"),

            ("human", """CONOCIMIENTO LOCAL (RAG):
            {context}

            CONOCIMIENTO EXTERNO (Ficha de personaje):
            {extra_info}

            PREGUNTA SOBRE MAGIA: {question}

            Instrucción final: Sé fiel al texto de los manuales. Si el RAG dice que una Bola de Fuego es una ESFERA, no digas que es un cono.""")
        ])

        chain = prompt | self.llm | StrOutputParser()

        # La invocación ahora es limpia y depende del estado que le pase el grafo
        answer = chain.invoke({
            "context": context,
            "extra_info": extra_info,
            "question": user_input,
            "lang": language,
            "chat_history": self.memory.messages
        })

        # Retornamos el formato esperado por el nodo de LangGraph
        return {"agent": "SpellMentor", "answer": answer}