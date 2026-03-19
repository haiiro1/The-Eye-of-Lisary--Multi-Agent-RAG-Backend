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
    ESTA VERSIÓN BLOQUEA EL BUCLE INFINITO.
    """
    # Si ya hay agentes en la cola, NO se clasifica,se dejan que fluyan.
    if state.get("selected_agents") and len(state["selected_agents"]) > 0:
        return {}

    last_msg = state["messages"][-1]
    # Extrae el contenido sin importar si es tupla o mensaje de LangChain
    content = last_msg[1] if isinstance(last_msg, tuple) else last_msg.content


    # Si el mensaje contiene etiquetas de expertos, significa que ya paso por ahí.
    expert_tags = ["[RULES_EXPERT]", "[SPELL_MENTOR]", "[CHAR_BUILDER]", "[WEB_EXPERT]", "[CHAT_EXPERT]"]

    if any(tag in content for tag in expert_tags):
        print("DEBUG: Detectado mensaje de experto. Limpiando cola para ir al agregador.")
        return {"selected_agents": []}

    # Si es un mensaje de un humano, clasificamos
    callbacks = config.get("callbacks", [])
    router = DnDRouter(callbacks=callbacks)

    # Se usa la función de ayuda que para obtener el texto limpio
    text = get_human_query(state["messages"])

    result = router.classify_intent(text)

    return {
        "selected_agents": result["intents"]
    }

def orchestrator(state: AgentState):
    # Obtenemos la lista actual de agentes pendientes
    pending = state.get("selected_agents", [])

    print(f"\n--- DEBUG ORQUESTADOR ---")
    print(f"Cola recibida: {pending}")

    if not pending:
        print("Resultado: Yendo a AGGREGATOR (Cola vacía)")
        return "aggregator"

    next_agent = str(pending[0]).lower().strip()

    print(f"Agente normalizado: '{next_agent}'")

    if next_agent in ["web", "builder", "rules", "spells", "chat"]:
        print(f"Resultado: Yendo a NODO '{next_agent}'")
        return next_agent

    print(f"Resultado: Yendo a AGGREGATOR (No reconocido)")
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

# Bordes condicionales y fijos
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

# El ciclo vuelve al router para consumir el siguiente agente de la lista
workflow.add_edge("web", "router_node")
workflow.add_edge("chat", "router_node")
workflow.add_edge("builder", "router_node")
workflow.add_edge("rules", "router_node")
workflow.add_edge("spells", "router_node")
workflow.add_edge("aggregator", END)

# --- EXPORTACIÓN ---
# Exportamos el objeto workflow para compilarlo con el checkpointer activo en la ejecución.
agent_workflow = workflow