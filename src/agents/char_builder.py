from src.core.base_agent import BaseDnDAgent
from src.tools.rag_tool import RAGTool
from src.agents.spell_mentor import SpellMentor
from src.agents.web_omni_expert import WebOmniExpert
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from src.core.logging_config import logger

class CharBuilder(BaseDnDAgent):
    def _setup_tools(self):
        return {
            "web_omni": WebOmniExpert(session_id=self.session_id),
            "rag": RAGTool(k=3),
            "spells": SpellMentor(session_id=self.session_id)
        }

    def run(self, user_input: str, language: str = "es") -> dict:
        logger.info(f"🏗️ [CharBuilder] Iniciando optimización de personaje con equipo unificado...")

        # 1. Búsqueda de Reglas Generales (Manuales Locales)
        official_context = self.tools["rag"].search(user_input)

        # 2. Apoyo de Expertos (Delegación)
        spell_advice = ""
        external_info = ""
        input_lower = user_input.lower()

        # Lógica para Magia: Delegamos al SpellMentor
        magic_keywords = ["hechizo", "spell", "magia", "lanzar", "slot", "conjuro", "cantrip"]
        if any(word in input_lower for word in magic_keywords):
            logger.info("🔮 [CharBuilder] Consultando al SpellMentor...")
            spell_res = self.tools["spells"].run(user_input, language=language)
            spell_advice = f"\n[CONSEJO MÁGICO]: {spell_res['answer']}"

        # Lógica para Contenido Externo: Delegamos al WebOmniExpert
        web_keywords = ["dandwiki", "homebrew", "wikidot", "oficial", "extra", "internet"]
        if any(word in input_lower for word in web_keywords):
            logger.info("🌐 [CharBuilder] Delegando búsqueda externa al WebOmniExpert...")
            web_res = self.tools["web_omni"].run(user_input, language=language)
            external_info = f"\n[INFO EXTERNA (Web)]: {web_res['answer']}"

        # 3. Prompt Maestro Universal
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres el Arquitecto de Almas, experto en la creación y optimización de personajes para D&D 5e.

             TUS PILARES DE CONSTRUCCIÓN:
             1. REGLAS OFICIALES: Valida dotes y rasgos usando el contexto de los manuales (RAG).
             2. INTEGRACIÓN WEB: Utiliza la INFO EXTERNA (Web) para añadir opciones de Wikidot o Dandwiki, manteniendo siempre el balance.
             3. OPTIMIZACIÓN MÁGICA: Incorpora el CONSEJO MÁGICO si el personaje es un lanzador de conjuros.
             4. HISTORIAL: Revisa la memoria de la sesión para mantener la coherencia con decisiones previas.

             Responde de forma técnica y motivadora en {lang}. Sirve para cualquier clase o nivel."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "DATOS TÉCNICOS:\n{context}\n{spell_info}\n{web_info}\n\nSOLICITUD: {question}")
        ])

        chain = prompt | self.llm | StrOutputParser()

        answer = chain.invoke({
            "context": official_context,
            "spell_info": spell_advice,
            "web_info": external_info,
            "question": user_input,
            "lang": language,
            "chat_history": self.memory.messages
        })

        self.memory.add_user_message(user_input)
        self.memory.add_ai_message(answer)

        return {"agent": "CharBuilder", "answer": answer}