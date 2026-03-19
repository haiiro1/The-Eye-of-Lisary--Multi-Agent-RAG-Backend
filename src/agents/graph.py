from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig
from src.core.state import AgentState
from src.agents.router import DnDRouter

# Importación de los nodos
from src.agents.nodes import (
    builder_node,
    chat_node,
    get_human_query,
    web_node,
    aggregator_node,
    rules_node,
    spell_node,
)

# --- NODOS DE CONTROL ---
def router_node(state: AgentState, config: RunnableConfig):
    """
    Analiza la entrada e inyecta callbacks.
    Mantiene la lógica de bloqueo de bucle para múltiples especialistas.
    """
    # Si ya hay agentes en la cola, NO se clasifica, se dejan que fluyan.
    if state.get("selected_agents") and len(state["selected_agents"]) > 0:
        return {}

    # Verificamos el último mensaje para evitar re-clasificar respuestas de expertos
    last_msg = state["messages"][-1]
    content = last_msg[1] if isinstance(last_msg, tuple) else last_msg.content

    # Etiquetas de control para detectar si el flujo ya pasó por un experto
    expert_tags = ["[RULES_EXPERT]", "[SPELL_MENTOR]", "[CHAR_BUILDER]", "[WEB_EXPERT]", "[CHAT_EXPERT]"]

    if any(tag in str(content) for tag in expert_tags):
        return {"selected_agents": []}

    # Clasificación inicial para mensajes humanos
    callbacks = config.get("callbacks", [])
    router = DnDRouter(callbacks=callbacks)
    text = get_human_query(state["messages"])
    result = router.classify_intent(text)

    return {
        "selected_agents": result["intents"]
    }

def orchestrator(state: AgentState):
    """Orquestador que decide el siguiente nodo basado en la cola selected_agents."""
    pending = state.get("selected_agents", [])

    if not pending:
        return "aggregator"

    next_agent = str(pending[0]).lower().strip()

    # Mapeo de intención a nombre de nodo
    if next_agent in ["web", "builder", "rules", "spells", "chat"]:
        return next_agent

    return "aggregator"

# --- DISEÑO DEL FLUJO ---
workflow = StateGraph(AgentState)

# Registro de Nodos
workflow.add_node("chat", chat_node)
workflow.add_node("router_node", router_node)
workflow.add_node("web", web_node)
workflow.add_node("builder", builder_node)
workflow.add_node("rules", rules_node)
workflow.add_node("spells", spell_node)
workflow.add_node("aggregator", aggregator_node)

workflow.set_entry_point("router_node")

workflow.add_conditional_edges(
    "router_node",
    orchestrator,
    {
        "web": "web",
        "builder": "builder",
        "rules": "rules",
        "spells": "spells",
        "chat": "chat",
        "aggregator": "aggregator"
    }
)

# Si es un saludo, el experto responde y termina el flujo.
workflow.add_edge("chat", END)

# Los especialistas técnicos sí vuelven al router por si hay más tareas
workflow.add_edge("web", "router_node")
workflow.add_edge("builder", "router_node")
workflow.add_edge("rules", "router_node")
workflow.add_edge("spells", "router_node")

workflow.add_edge("aggregator", END)

agent_workflow = workflow