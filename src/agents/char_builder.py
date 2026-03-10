from src.core.base_agent import BaseDnDAgent
from src.tools.rag_tool import RAGTool
from src.tools.CombatCalculatorTool import CombatCalculatorTool
from src.tools.sheet_manager import SheetManager
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from src.core.logging_config import logger

class CharBuilder(BaseDnDAgent):
    def _setup_tools(self):
        return {
            "rag": RAGTool(k=3),# 3 chunks, fragmentos más parecidos para tener un contexto amplio sin saturar
            "sheet": SheetManager(),
            "calculator": CombatCalculatorTool()
        }

    def run(self, user_input: str, language: str = "es", extra_context: str = "") -> dict:
        logger.info(f"🏗️ [CharBuilder] Optimizando personaje en modo nodo...")

        # 1. Búsqueda en manuales locales
        official_context = self.tools["rag"].search(user_input)

        # 2. Prompt Maestro (Adaptado para recibir contexto extra del grafo)
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres el Arquitecto de Almas, experto en creación y optimización para D&D 5e.

             PILARES:
             1. REGLAS OFICIALES: Usa el contexto de manuales (RAG).
             2. BALANCE: Mantén la coherencia técnica.
             3. IDIOMA: Responde en {lang}.

             Si el contexto extra contiene consejos de otros expertos, intégralos de forma fluida."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "DATOS LOCALES:\n{context}\n\nINFORMACIÓN EXTRA:\n{extra_info}\n\nSOLICITUD: {question}")
        ])

        chain = prompt | self.llm | StrOutputParser()

        # El historial de mensajes se maneja ahora por LangGraph en el estado
        answer = chain.invoke({
            "context": official_context,
            "extra_info": extra_context,
            "question": user_input,
            "lang": language,
            "chat_history": self.memory.messages
        })

        # Nota: La persistencia en memoria ahora la puede gestionar LangGraph automáticamente
        return {"agent": "CharBuilder", "answer": answer}