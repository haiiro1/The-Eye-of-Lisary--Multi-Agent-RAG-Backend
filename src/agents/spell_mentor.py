from src.core.base_agent import BaseDnDAgent
from src.tools.rag_tool import RAGTool
from src.agents.web_omni_expert import WebOmniExpert
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from src.core.logging_config import logger

class SpellMentor(BaseDnDAgent):
    def _setup_tools(self):
        # El mentor usa RAG para manuales locales y delega al WebOmni para lo externo
        return {
            "rag": RAGTool(k=3),
            "web_omni": WebOmniExpert(session_id=self.session_id)
        }

    def run(self, user_input: str, language: str = "es") -> dict:
        logger.info(f"🧙‍♂️ [SpellMentor] Analizando conocimientos arcanos...")

        # 1. Buscamos en los manuales locales (RAG)
        context = self.tools["rag"].search(user_input)
        # 2. Apoyo dinámico del WebOmniExpert si no hay info local suficiente
        # O si se menciona explícitamente contenido de expansiones/web
        extra_web_info = ""
        if len(context) < 200 or any(w in user_input.lower() for w in ["wikidot", "dandwiki", "homebrew", "tasha", "xanathar"]):
            logger.info("🌐 [SpellMentor] Consultando al WebOmniExpert para ampliar el libro de conjuros...")
            web_res = self.tools["web_omni"].run(user_input, language=language)
            extra_web_info = f"\n[CONOCIMIENTO DE GRIMORIOS EXTERNOS]: {web_res['answer']}"

        # 3. Prompt Maestro Arcano
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres el Mentor de Hechizos del Ojo de Lisary, una autoridad en artes arcanas y divinas.
             Tu misión es explicar la magia de D&D 5e con precisión técnica y visión estratégica.

             PROTOCOLOS DE ENSEÑANZA:
             1. FICHA TÉCNICA: Indica siempre Tiempo de lanzamiento, Alcance, Componentes (V, S, M) y Duración.
             2. CONCENTRACIÓN: Si el hechizo la requiere, advierte claramente sobre los riesgos de perderla y cómo afecta a otros hechizos activos.
             3. IDIOMA: Responde en {lang}. Si el nombre original es inglés, úsalo entre paréntesis: 'Paso Misterioso (Misty Step)'.
             4. ESTRATEGIA: Sugiere combinaciones con otros rasgos o hechizos si el historial de chat muestra que el personaje tiene sinergias.
             5. AGNOSTICISMO: Sirve a cualquier lanzador de conjuros, adaptando tu consejo a su nivel y clase detectados."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "CONOCIMIENTO LOCAL (RAG):\n{context}\n{extra_info}\n\nPREGUNTA SOBRE MAGIA: {question}")
        ])

        chain = prompt | self.llm | StrOutputParser()
        answer = chain.invoke({
            "context": context,
            "extra_info": extra_web_info,
            "question": user_input,
            "lang": language,
            "chat_history": self.memory.messages
        })

        self.memory.add_user_message(user_input)
        self.memory.add_ai_message(answer)
        return {"agent": "SpellMentor", "answer": answer}