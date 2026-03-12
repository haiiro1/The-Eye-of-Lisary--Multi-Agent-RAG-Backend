from src.agents.rules_expert import RulesExpert
from src.agents.char_builder import CharBuilder
from src.agents.spell_mentor import SpellMentor
from src.agents.web_omni_expert import WebOmniExpert
from src.core.factory import LLMFactory
from src.core.state import AgentState
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

def _get_text(message):
    """Extrae texto de tuplas ('role', 'content') o mensajes de LangChain."""
    if isinstance(message, tuple):
        return message[1]
    if hasattr(message, 'content'):
        return message.content
    return str(message)

# --- NODO: WEB/WIKI (Especialista Principal Actual) ---
def web_node(state: AgentState):
    user_input = _get_text(state["messages"][-1])
    expert = WebOmniExpert(session_id="lg_session")

    # Se le da contexto de D&D 5e para búsquedas más precisas
    result = expert.run(
        user_input=f"Consulta D&D 5e: {user_input}",
        language=state.get("language", "es")
    )

    return {
        "messages": [("assistant", f"[WEB_EXPERT]: {result['answer']}")]
    }

# --- NODO: CONSTRUCCIÓN/FICHAS ---
def builder_node(state: AgentState):
    user_input = _get_text(state["messages"][-1])
    expert = CharBuilder(session_id="lg_session")

    result = expert.run(
        user_input=user_input,
        language=state.get("language", "es")
    )

    # prefijos temporales como [WEB_EXPERT] o [CHAR_BUILDER] en los mensajes de los nodos intermedios.
    # Esto ayuda al aggregator_node a saber de dónde viene cada dato para mezclarlos mejor
    return {
        "messages": [("assistant", f"[CHAR_BUILDER]: {result['answer']}")]
    }

# --- NODO: AGREGADOR (Unificador de respuestas) ---
def aggregator_node(state: AgentState):
    """
    Nodo Narrador: Transforma los reportes técnicos de los especialistas 
    en una respuesta inmersiva y coherente.
    """
    llm = LLMFactory.get_model(is_reasoning=False)

    # Preparamos un prompt con personalidad
    prompt = ChatPromptTemplate.from_template("""
        Eres el 'Ojo de Lisary', un artefacto arcano sensible que guía a los aventureros en D&D 5e.
        Tu tono es sabio, ligeramente místico pero muy claro y útil.

        Misión:
        Has recibido datos de tus 'visiones' (especialistas internos). Debes unificarlos
        en una sola respuesta coherente para el usuario.

        Reglas de Oro:
        1. NUNCA menciones a los especialistas, ni digas "según la web" o "el constructor dice".
        2. ELIMINA etiquetas como [WEB_EXPERT], [CHAR_BUILDER] o [RULES_EXPERT].
        3. Si hay datos de la ficha y de reglas, combínalos. (Ej: "Veo en tus registros que tienes +5 en Atletismo, por lo que saltar ese foso será...")
        4. Responde siempre en {language}.

        Información recolectada de las visiones:
        {messages}

        Respuesta final para el aventurero:
    """)

    chain = prompt | llm | StrOutputParser()

    # Invocamos la unificación
    unified_answer = chain.invoke({
        "messages": state["messages"],
        "language": state.get("language", "es")
    })

    # Retornamos el mensaje final y vaciamos la cola de agentes por si acaso
    return {
        "messages": [("assistant", unified_answer)],
        "selected_agents": []
    }

# --- NODOS EN RESERVA (Opcionales por ahora) ---
def rules_node(state: AgentState):
    user_input = _get_text(state["messages"][-1])
    expert = RulesExpert(session_id="lg_session")
    result = expert.run(user_input=user_input, language=state.get("language", "es"))
    return {"messages": [("assistant", f"[RULES_EXPERT]: {result['answer']}")]}

def spell_node(state: AgentState):
    user_input = _get_text(state["messages"][-1])
    expert = SpellMentor(session_id="lg_session")
    result = expert.run(user_input=user_input, language=state.get("language", "es"))
    return {"messages": [("assistant", f"[SPELL_MENTOR]: {result['answer']}")]}