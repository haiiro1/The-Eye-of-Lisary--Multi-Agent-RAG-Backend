from src.core.base_agent import BaseDnDAgent
from src.tools.rag_tool import RAGTool
from src.tools.wiki_tool import WikiTool
from src.agents.spell_mentor import SpellMentor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from src.core.logging_config import logger

class RulesExpert(BaseDnDAgent):
    def _setup_tools(self):
        # El experto en reglas ahora tiene el arsenal completo para validar dudas
        return {
            "wiki": WikiTool(),
            "rag": RAGTool(k=4),
            "spells": SpellMentor(session_id=self.session_id),
        }

    def run(self, user_input: str, language: str = "es") -> dict:
        logger.info(f"⚖️ [RulesExpert] Resolviendo duda reglamentaria...")

        # 1. Obtener contexto de los manuales locales (RAG)
        context_rag = self.tools["rag"].search(user_input)

        # 2. Apoyo dinámico de Magia o Web si la duda lo requiere
        extra_info = ""
        input_lower = user_input.lower()

        # Si la duda es sobre hechizos, llamamos al mentor
        if any(w in input_lower for w in ["hechizo", "spell", "magia", "lanzar", "concentración"]):
            spell_res = self.tools["spells"].run(user_input, language=language)
            extra_info += f"\n[ACLARACIÓN MÁGICA]: {spell_res['answer']}"

        # Si la duda menciona contenido externo o expansiones
        if any(w in input_lower for w in ["wikidot", "oficial", "errata", "sage advice"]):
            web_res = self.tools["wiki"].search_wikidot(user_input)
            extra_info += f"\n[INFO WEB OFICIAL]: {web_res}"

        # 3. El Prompt Maestro
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres el Juez Supremo de Reglas del Ojo de Lisary.
             Tu misión es resolver cualquier duda sobre mecánicas de D&D 5e de forma imparcial y técnica.

             DIRECTRICES DE JUICIO:
             1. REGLAS ESCRITAS (RAW): Prioriza siempre lo que dicen los MANUALES proporcionados.
             2. REGLAS SEGÚN LA INTENCIÓN (RAI): Si el manual es ambiguo, usa la INFO WEB o el CONSEJO MÁGICO para ofrecer la interpretación más lógica.
             3. IDIOMA: Responde con autoridad y claridad en {lang}.
             4. ESTRUCTURA: Usa negritas para términos mecánicos (ej: **Ventaja**, **Acción Adicional**, **Salvación de Destreza**).
             5. AGNOSTICISMO: No asumas que hablas de un personaje específico a menos que el historial lo indique. Tu respuesta debe servir para cualquier mesa de juego."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "CONTEXTO REGLAMENTARIO:\n{context}\n{extra_info}\n\nPREGUNTA DEL JUGADOR: {question}")
        ])

        chain = prompt | self.llm | StrOutputParser()
        answer = chain.invoke({
            "context": context_rag,
            "extra_info": extra_info,
            "question": user_input,
            "lang": language,
            "chat_history": self.memory.messages
        })

        self.memory.add_user_message(user_input)
        self.memory.add_ai_message(answer)

        return {"agent": "RulesExpert", "answer": answer}