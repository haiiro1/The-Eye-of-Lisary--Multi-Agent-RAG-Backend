from src.core.factory import LLMFactory
from src.agents.rules_expert import RulesExpert
from src.agents.char_builder import CharBuilder
from src.agents.spell_mentor import SpellMentor
from src.agents.web_omni_expert import WebOmniExpert # Único experto web necesario
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.core.logging_config import logger

class DnDRouter:
    def __init__(self):
        # Usamos el modelo de routing (más rápido) para clasificar
        self.llm = LLMFactory.get_model(is_reasoning=False)
        self.agents = {}

    def route(self, user_input: str, session_id: str, sheet_context: str = None):
        logger.info(f"🔮 Analizando entrada para sesión {session_id}...")

        # 1. Detectar Idioma (ISO Code)
        lang_prompt = f"Identify the ISO language code (e.g., 'es', 'en'). Reply ONLY with the code: {user_input}"
        user_lang = self.llm.invoke(lang_prompt).content.strip().lower()[:2]
        logger.info(f"🌐 Idioma detectado: {user_lang}")

        # 2. Lógica de Prioridad para la Ficha
        # Evita alucinaciones web si el usuario habla claramente de su personaje.
        keywords_ficha = ["mi", "mis", "yo", "tengo", "wade", "personaje", "ataque", "daño", "stats", "ficha"]
        input_lower = user_input.lower()

        if sheet_context and sheet_context != "No hay ficha cargada." and any(word in input_lower for word in keywords_ficha):
            decision = "SHEET"
            logger.info("🎯 Prioridad detectada: Derivando al SheetExpert.")
        else:
            # 3. Clasificación de Intención Unificada
            prompt = ChatPromptTemplate.from_template("""
                Clasifica la intención del usuario para un sistema de D&D 5e:
                - 'SHEET': Preguntas sobre las estadísticas o equipo del personaje actual.
                - 'RULES': Reglas generales de los manuales (combate, acciones, estados).
                - 'WEB': Consultas sobre contenido externo, expansiones (Wikidot) o Homebrew (Dandwiki).
                - 'SPELLS': Información sobre hechizos, slots o magia.
                - 'BUILDER': Creación de personajes o guía para subir de nivel.
                - 'CHAT': Saludos, despedidas o charla informal.

                Responde ÚNICAMENTE con la palabra de la etiqueta en mayúsculas.
                Mensaje del usuario: {input}
            """)
            decision = (prompt | self.llm | StrOutputParser()).invoke({"input": user_input}).strip().upper()

        logger.info(f"🎯 Decisión final del Router: {decision}")

        # 4. Orquestación de Agentes
        try:

            if "WEB" in decision:
                if "web_omni" not in self.agents: self.agents["web_omni"] = WebOmniExpert(session_id=session_id)
                return self.agents["web_omni"].run(user_input, language=user_lang)

            elif "SPELLS" in decision:
                if "spells" not in self.agents: self.agents["spells"] = SpellMentor(session_id=session_id)
                return self.agents["spells"].run(user_input, language=user_lang)

            elif "RULES" in decision:
                if "rules" not in self.agents: self.agents["rules"] = RulesExpert(session_id=session_id)
                return self.agents["rules"].run(user_input, language=user_lang)

            elif "BUILDER" in decision:
                if "builder" not in self.agents: self.agents["builder"] = CharBuilder(session_id=session_id)
                return self.agents["builder"].run(user_input, language=user_lang)

        except Exception as e:
            logger.error(f"❌ Error al derivar al agente {decision}: {e}")
            return {"agent": "Router", "answer": "Hubo un problema al consultar al experto. ¿Podrías repetir la pregunta?"}

        # Respuesta por defecto para CHAT o decisiones no reconocidas
        msg = "¡Saludos! Soy el Ojo de Lisary. ¿En qué puedo ayudarte hoy?" if user_lang == "es" else "Greetings! I am the Eye of Lisary. How can I assist you today?"
        return {"agent": "Router-Chat", "answer": msg}