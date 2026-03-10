from src.core.base_agent import BaseDnDAgent
from src.tools.rag_tool import RAGTool
from src.agents.spell_mentor import SpellMentor
from src.agents.web_omni_expert import WebOmniExpert
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from src.core.logging_config import logger

class RulesExpert(BaseDnDAgent):
    def _setup_tools(self):
        # Unificamos: El experto en reglas usa RAG para lo local y WebOmni para lo externo
        return {
            "rag": RAGTool(k=4),
            "web_omni": WebOmniExpert(session_id=self.session_id),
            "spells": SpellMentor(session_id=self.session_id),
        }

    def run(self, user_input: str, language: str = "es") -> dict:
        logger.info(f"⚖️ [RulesExpert] Resolviendo duda reglamentaria con apoyo unificado...")

        # 1. Obtener contexto de los manuales locales (RAG)
        context_rag = self.tools["rag"].search(user_input)

        # 2. Apoyo dinámico de Magia o Web a través de Agentes Especializados
        extra_info = ""
        input_lower = user_input.lower()

        # Si la duda es sobre hechizos, delegamos al SpellMentor
        if any(w in input_lower for w in ["hechizo", "spell", "magia", "lanzar", "concentración"]):
            spell_res = self.tools["spells"].run(user_input, language=language)
            extra_info += f"\n[ACLARACIÓN MÁGICA]: {spell_res['answer']}"

        # CORRECCIÓN: Si la duda requiere internet, delegamos al WebOmniExpert
        # Ya no usamos WikiTool directamente, usamos el agente unificado.
        keywords_web = ["wikidot", "dandwiki", "oficial", "errata", "sage advice", "homebrew"]
        if any(w in input_lower for w in keywords_web):
            logger.info(f"🌐 [RulesExpert] Delegando búsqueda externa al WebOmniExpert...")
            web_res = self.tools["web_omni"].run(user_input, language=language)
            extra_info += f"\n[INFO EXTERNA (Web)]: {web_res['answer']}"

        # 3. El Prompt Maestro (Agnóstico y Profesional)
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres el Juez Supremo de Reglas del Ojo de Lisary.
             Tu misión es resolver dudas sobre mecánicas de D&D 5e de forma imparcial y técnica.

             DIRECTRICES DE JUICIO:
             1. RAW (Reglas Escritas): Prioriza siempre los MANUALES locales.
             2. RAI (Reglas según Intención): Usa la INFO EXTERNA o ACLARACIÓN MÁGICA para interpretar ambigüedades.
             3. IDIOMA: Responde con autoridad en {lang}.
             4. FORMATO: Usa negritas para términos mecánicos (**Acción**, **Salvación**, **Ventaja**).
             5. AGNOSTICISMO: Tu respuesta debe ser válida para cualquier mesa de juego."""),
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