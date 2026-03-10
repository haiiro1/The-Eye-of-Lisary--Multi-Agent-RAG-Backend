from src.agents.rules_expert import RulesExpert
from src.agents.char_builder import CharBuilder
from src.agents.spell_mentor import SpellMentor
from src.agents.web_omni_expert import WebOmniExpert
from src.core.state import AgentState

def _get_text(message):
    """Función auxiliar para extraer texto de tuplas o mensajes de LangChain."""
    if isinstance(message, tuple):
        return message[1]
    if hasattr(message, 'content'):
        return message.content
    return str(message)

# --- NODO: REGLAS ---
def rules_node(state: AgentState):
    user_input = _get_text(state["messages"][-1])
    expert = RulesExpert(session_id="lg_session")

    result = expert.run(
        user_input=user_input,
        language=state.get("language", "es"),
        extra_info=state.get("sheet_context", "")
    )

    return {
        "messages": [("assistant", result["answer"])],
        "next_step": "RulesExpert"
    }

# --- NODO: CONSTRUCCIÓN/FICHAS ---
def builder_node(state: AgentState):
    user_input = _get_text(state["messages"][-1])
    expert = CharBuilder(session_id="lg_session")

    result = expert.run(
        user_input=user_input,
        language=state.get("language", "es")
    )

    return {
        "messages": [("assistant", result["answer"])],
        "next_step": "CharBuilder"
    }

# --- NODO: HECHIZOS ---
def spell_node(state: AgentState):
    user_input = _get_text(state["messages"][-1])
    expert = SpellMentor(session_id="lg_session")

    result = expert.run(
        user_input=user_input,
        language=state.get("language", "es")
    )

    return {
        "messages": [("assistant", result["answer"])],
        "next_step": "SpellMentor"
    }

# --- NODO: WEB/WIKI ---
def web_node(state: AgentState):
    user_input = _get_text(state["messages"][-1])
    # Instanciamos el experto web
    expert = WebOmniExpert(session_id="lg_session")

    # Podemos pasarle un 'hint' interno o contexto para que sepa
    # que debe buscar reglas oficiales de D&D 5e específicamente.
    result = expert.run(
        user_input=f"Reglas oficiales D&D 5e: {user_input}",
        language=state.get("language", "es")
    )

    # El asistente responderá usando Tavily/Google Search
    return {
        "messages": [("assistant", result["answer"])],
        "next_step": "WebOmniExpert"
    }