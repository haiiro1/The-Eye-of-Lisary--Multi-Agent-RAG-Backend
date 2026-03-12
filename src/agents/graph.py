from langgraph.graph import StateGraph, END
from src.core.state import AgentState
from src.agents.nodes import builder_node, web_node, aggregator_node
from src.agents.router import DnDRouter

def router_node(state: AgentState):
    """Analiza la entrada y decide qué especialistas se necesitan."""
    router = DnDRouter()
    last_msg = state["messages"][-1]
    text = last_msg[1] if isinstance(last_msg, tuple) else last_msg.content

    result = router.classify_intent(text)
    return {"selected_agents": result["intents"]}

def orchestrator(state: AgentState):
    """Controlador de flujo que consume la lista selected_agents."""
    pending = state.get("selected_agents", [])

    if not pending:
        return "aggregator"

    # Extrae el siguiente agente de la lista
    next_agent = pending.pop(0).lower()

    # Mapeo dinámico a los nodos disponibles
    if next_agent in ["web", "builder"]:
        return next_agent

    return "aggregator"

# Configuración del diseño del grafo
workflow = StateGraph(AgentState)

workflow.add_node("router_node", router_node)
workflow.add_node("web", web_node)
workflow.add_node("builder", builder_node)
workflow.add_node("aggregator", aggregator_node)

workflow.set_entry_point("router_node")

workflow.add_conditional_edges(
    "router_node",
    orchestrator,
    {
        "web": "web",
        "builder": "builder",
        "aggregator": "aggregator"
    }
)

# Los nodos vuelven al router para verificar si hay más agentes en la cola
workflow.add_edge("web", "router_node")
workflow.add_edge("builder", "router_node")
workflow.add_edge("aggregator", END)