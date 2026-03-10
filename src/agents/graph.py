from langgraph.graph import StateGraph, END
from src.core.state import AgentState
from src.agents.nodes import rules_node, builder_node, spell_node, web_node
from src.agents.router import DnDRouter
from src.core.memory import get_graph_checkpointer
from src.core.logging_config import logger

def router_logic(state: AgentState):
    """
    Controlador que contextualiza y redirige temporalmente SPELLS/RULES a WEB.
    """
    last_msg = state["messages"][-1]
    user_text = last_msg[1] if isinstance(last_msg, tuple) else last_msg.content

    router = DnDRouter()

    # 1. Clasificación y Contextualización
    classification = router.classify_intent(
        user_input=user_text,
        messages=state["messages"],
        sheet_context=state.get("sheet_context", "")
    )

    # 2. Actualizar el mensaje con la pregunta limpia
    contextualized_text = classification.get("contextualized_input", user_text)
    state["messages"][-1] = ("human", contextualized_text)

    # 3. Lógica de Enrutamiento con REDIRECCIÓN TEMPORAL
    raw_intent = classification.get("intent", "RULES").upper()

    logger.info(f"🚦 [Router Logic] Intención detectada: {raw_intent}")

    # --- ESTRATEGIA WEB-FIRST ---
    # Si es SPELLS o RULES, ignoramos el RAG local y vamos a la WEB
    if raw_intent in ["SPELLS", "RULES", "WEB"]:
        logger.info("🌐 [Router Logic] Redirigiendo a WebOmni por mantenimiento de RAG local.")
        return "web"

    if "BUILDER" in raw_intent:
        return "builder"

    if "CHAT" in raw_intent:
        return "end"

    # Fallback de seguridad
    return "web"

# --- Construcción del Grafo ---
workflow = StateGraph(AgentState)

workflow.add_node("rules", rules_node)
workflow.add_node("builder", builder_node)
workflow.add_node("spells", spell_node)
workflow.add_node("web", web_node)

workflow.set_conditional_entry_point(
    router_logic,
    {
        "rules": "rules",    # Mantenemos el mapeo por si acaso, aunque router_logic no lo use ahora
        "builder": "builder",
        "spells": "spells",
        "web": "web",
        "end": END
    }
)

# Edges
workflow.add_edge("rules", END)
workflow.add_edge("builder", END)
workflow.add_edge("spells", END)
workflow.add_edge("web", END)

app_graph = workflow.compile(checkpointer=get_graph_checkpointer())