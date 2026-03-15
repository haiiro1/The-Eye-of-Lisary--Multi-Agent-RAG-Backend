from langgraph.graph import StateGraph, END
from src.core.state import AgentState
from src.agents.nodes import (
    builder_node,
    web_node,
    aggregator_node,
    rules_node,
    spell_node,
)
from src.agents.router import DnDRouter

def router_node(state: AgentState):
    """
    Analiza la entrada del usuario (si es el inicio) o verifica
    la cola de agentes seleccionados.
    """
    # Si ya hay agentes seleccionados, no volvemos a clasificar (evita bucles)
    if state.get("selected_agents"):
        return {"selected_agents": state["selected_agents"]}

    router = DnDRouter()
    last_msg = state["messages"][-1]
    text = last_msg[1] if isinstance(last_msg, tuple) else last_msg.content

    # Clasificamos la intención por primera vez
    result = router.classify_intent(text)

    return {
        "selected_agents": result["intents"]
    }

def orchestrator(state: AgentState):
    """
    Controlador de flujo que consume la cola de 'selected_agents'.
    Si la lista está vacía, finaliza en el agregador.
    """
    pending = state.get("selected_agents", [])

    if not pending:
        return "aggregator"

    # Extrae el siguiente agente de la lista (ej: "builder", "spells")
    next_agent = pending.pop(0).lower()

    # Mapeo dinámico a los nodos registrados
    if next_agent in ["web", "builder", "rules", "spells"]:
        return next_agent

    return "aggregator"

# --- DISEÑO DEL FLUJO ---
workflow = StateGraph(AgentState)

# Registro de Nodos
workflow.add_node("router_node", router_node)
workflow.add_node("web", web_node)
workflow.add_node("builder", builder_node)
workflow.add_node("rules", rules_node)
workflow.add_node("spells", spell_node)
workflow.add_node("aggregator", aggregator_node)

# Configuración de entrada
workflow.set_entry_point("router_node")

# Bordes condicionales desde el router
workflow.add_conditional_edges(
    "router_node",
    orchestrator,
    {
        "web": "web",
        "builder": "builder",
        "rules": "rules",
        "spells": "spells",
        "aggregator": "aggregator"
    }
)

# REGLA CRÍTICA: Los especialistas vuelven al router para ver si hay 
# más agentes pendientes en la cola (selected_agents)
workflow.add_edge("web", "router_node")
workflow.add_edge("builder", "router_node")
workflow.add_edge("rules", "router_node")
workflow.add_edge("spells", "router_node")

# El agregador es el fin del camino
workflow.add_edge("aggregator", END)

# Compilación
app = workflow.compile()