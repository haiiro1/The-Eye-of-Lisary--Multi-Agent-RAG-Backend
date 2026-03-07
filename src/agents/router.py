from src.agents.sheet_expert import SheetExpert
from src.core.factory import LLMFactory
from src.agents.rules_expert import RulesExpert
from src.agents.char_builder import CharBuilder
from src.agents.spell_mentor import SpellMentor
from src.agents.official_web_expert import OfficialWebExpert
from src.agents.homebrew_expert import HomebrewExpert
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.core.logging_config import logger

class DnDRouter:
    def __init__(self):
        self.llm = LLMFactory.get_model(is_reasoning=False)
        self.agents = {}

    def route(self, user_input: str, session_id: str, sheet_context: str = None):
        logger.info(f"🔮 Analizando entrada para sesión {session_id}...")

        # 1. Detectar Idioma
        lang_prompt = f"Identify the ISO language code (e.g., 'es', 'en'). Reply ONLY with the code: {user_input}"
        user_lang = self.llm.invoke(lang_prompt).content.strip().lower()[:2]
        logger.info(f"🌐 Idioma detectado: {user_lang}")

        # 2. Lógica de Prioridad para la Ficha (Evita que el OfficialWebExpert alucine)
        # Si hay contexto de ficha y el usuario usa posesivos o nombres propios, forzamos SHEET.
        keywords_ficha = ["mi", "mis", "yo", "tengo", "wade", "personaje", "ataque", "daño", "stats"]
        input_lower = user_input.lower()

        if sheet_context and any(word in input_lower for word in keywords_ficha):
            decision = "SHEET"
            logger.info("🎯 Prioridad detectada: Consultando directamente la ficha del personaje.")
        else:
            # 3. Clasificación de Intención por IA (si no se forzó SHEET)
            prompt = ChatPromptTemplate.from_template("""
                Clasifica la intención del usuario (D&D 5e):
                - 'SHEET': Estadísticas, equipo o habilidades del personaje actual (Wade).
                - 'RULES': Reglas generales de manuales PDFs.
                - 'OFFICIAL_WEB': Buscar en Wikidot reglas oficiales externas.
                - 'HOMEBREW': Dandwiki o contenido creado por fans.
                - 'SPELLS': Consultas sobre hechizos específicos.
                - 'BUILDER': Creación o subida de nivel de personajes.
                - 'CHAT': Saludos o charla casual.

                Responde solo con la etiqueta en mayúsculas.
                Mensaje: {input}
            """)
            decision = (prompt | self.llm | StrOutputParser()).invoke({"input": user_input}).strip().upper()

        logger.info(f"🎯 Decisión final del Router: {decision}")

        # 4. Derivación con pase de datos
        if "SHEET" in decision:
            if "sheet" not in self.agents: self.agents["sheet"] = SheetExpert(session_id=session_id)
            return self.agents["sheet"].run(user_input, sheet_context=sheet_context, language=user_lang)

        elif "OFFICIAL_WEB" in decision:
            if "official" not in self.agents: self.agents["official"] = OfficialWebExpert(session_id=session_id)
            return self.agents["official"].run(user_input, language=user_lang)

        elif "HOMEBREW" in decision:
            if "homebrew" not in self.agents: self.agents["homebrew"] = HomebrewExpert(session_id=session_id)
            return self.agents["homebrew"].run(user_input, language=user_lang)

        elif "SPELLS" in decision:
            if "spells" not in self.agents: self.agents["spells"] = SpellMentor(session_id=session_id)
            return self.agents["spells"].run(user_input, language=user_lang)

        elif "RULES" in decision:
            if "rules" not in self.agents: self.agents["rules"] = RulesExpert(session_id=session_id)
            return self.agents["rules"].run(user_input, language=user_lang)

        elif "BUILDER" in decision:
            if "builder" not in self.agents: self.agents["builder"] = CharBuilder(session_id=session_id)
            return self.agents["builder"].run(user_input, language=user_lang)

        # Respuesta por defecto
        msg = "¡Saludos! Soy el Ojo de Lisary. ¿Quieres saber algo de Wade o buscamos reglas en Wikidot?" if user_lang == "es" else "Greetings! I am the Eye of Lisary. Shall we check Wade's stats or look up rules in Wikidot?"
        return {"agent": "Router-Chat", "answer": msg}