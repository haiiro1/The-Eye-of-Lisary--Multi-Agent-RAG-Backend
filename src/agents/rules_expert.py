from src.core.base_agent import BaseDnDAgent
from src.tools.rag_tool import RAGTool
from src.tools.ConditionExpertTool import ConditionExpertTool
from src.tools.CombatCalculatorTool import CombatCalculatorTool
from src.tools.DiceRollerTool import DiceRollerTool
# ELIMINADO: Ya no importa ni instancia otros agentes directamente
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from src.core.logging_config import logger

class RulesExpert(BaseDnDAgent):
    def _setup_tools(self):
        # Ahora el experto solo se encarga de los manuales oficiales mediante RAG
        return {
            "rag": RAGTool(k=4),
            "conditions": ConditionExpertTool(),
            "calculator": CombatCalculatorTool(),
            "dice": DiceRollerTool(),
        }

    def run(self, user_input: str, language: str = "es", extra_info: str = "") -> dict:
        logger.info(f"⚖️ [RulesExpert] Resolviendo duda reglamentaria en modo nodo...")

        # 1. Obtener contexto de los manuales locales (RAG)
        context_rag = self.tools["rag"].search(user_input)

        # 2. El Prompt Maestro (Agnóstico y Profesional)
        # Se mantiene la capacidad de recibir 'extra_info' desde el grafo si otros nodos aportaron algo
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres el Juez Supremo de Reglas.

             PROTOCOLOS DE JUICIO:
             1. ESTADOS: Si la duda es sobre condiciones (Cegado, Apresado, etc.), usa la lógica de tu herramienta de CONDICIONES.
             2. MATEMÁTICAS: Para CA, CD de salvación o bonos de ataque, utiliza tu CALCULADORA de combate. No inventes números.
             3. AZAR: Si el jugador pide una tirada, usa tu herramienta de DADOS.
             4. RAW: Prioriza los MANUALES (RAG) para reglas generales.
             5. Responde con autoridad técnica en {lang}, usando negritas para términos mecánicos."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "CONTEXTO REGLAMENTARIO:\n{context}\n\nINFO EXTRA:\n{extra_info}\n\nPREGUNTA: {question}")
        ])

        chain = prompt | self.llm | StrOutputParser()

        # Invocamos la cadena. La memoria ahora se gestiona de forma externa o mediante el estado del grafo.
        answer = chain.invoke({
            "context": context_rag,
            "extra_info": extra_info,
            "question": user_input,
            "lang": language,
            "chat_history": self.memory.messages
        })

        # Nota: En LangGraph, podrías elegir no añadir los mensajes aquí y dejar que el Grafo lo haga.
        return {"agent": "RulesExpert", "answer": answer}