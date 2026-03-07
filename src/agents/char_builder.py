from src.core.base_agent import BaseDnDAgent
from src.tools.wiki_tool import WikiTool
from src.tools.rag_tool import RAGTool
from src.agents.spell_mentor import SpellMentor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from src.core.logging_config import logger

class CharBuilder(BaseDnDAgent):
    def _setup_tools(self):
        return {
            "wiki": WikiTool(),
            "rag": RAGTool(k=3),
            "spells": SpellMentor(session_id=self.session_id)
        }

    def run(self, user_input: str, language: str = "es") -> dict:
        logger.info(f"🏗️ [CharBuilder] Iniciando construcción/optimización de personaje...")

        # 1. Búsqueda de Reglas Generales (RAG)
        # Esto sirve para cualquier clase o raza oficial
        official_context = self.tools["rag"].search(user_input)

        # 2. Lógica de Apoyo Mágico Dinámica
        # Si la entrada sugiere magia, consultamos al experto en hechizos
        spell_advice = ""
        magic_keywords = ["hechizo", "spell", "magia", "lanzar", "slot", "conjuro", "cantrip"]
        if any(word in user_input.lower() for word in magic_keywords):
            logger.info("🔮 [CharBuilder] Consultando al SpellMentor para apoyo arcano...")
            spell_res = self.tools["spells"].run(user_input, language=language)
            spell_advice = f"\n[CONSEJO MÁGICO]: {spell_res['answer']}"

        # 3. Prompt Universal
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres el Arquitecto de Almas, experto en la creación y optimización de personajes para D&D 5e.

             TUS PILARES:
             1. REGLAS OFICIALES: Usa el contexto de los manuales (RAG) para validar dotes, multiclases y rasgos.
             2. CONTENIDO EXTERNO: Si el usuario menciona 'Dandwiki' o 'Homebrew', usa tu conocimiento web para integrarlo, advirtiendo siempre sobre el equilibrio del juego.
             3. SINERGIA MÁGICA: Si se proporciona consejo del Mentor de Hechizos, intégralo para optimizar el repertorio del personaje.
             4. PERSONALIZACIÓN: Analiza las estadísticas actuales del personaje (si están en el historial) para sugerir la mejor ruta de progresión.

             Responde de forma inspiradora y técnica en {lang}. No te limites a un solo personaje; sirve para cualquier clase, raza o nivel."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "CONTEXTO TÉCNICO:\n{context}\n{spell_info}\n\nSOLICITUD DEL JUGADOR: {question}")
        ])

        chain = prompt | self.llm | StrOutputParser()

        answer = chain.invoke({
            "context": official_context,
            "spell_info": spell_advice,
            "question": user_input,
            "lang": language,
            "chat_history": self.memory.messages
        })

        self.memory.add_user_message(user_input)
        self.memory.add_ai_message(answer)

        return {"agent": "CharBuilder", "answer": answer}