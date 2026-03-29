import logging
from typing import List, Union
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import BaseMessage

from src.core.state import AgentState
from src.agents.router import DnDRouter

# Importación de los nodos especialistas
from src.agents.nodes import (
    builder_node,
    chat_node,
    get_human_query,
    web_node,
    aggregator_node,
    rules_node,
    spell_node,
)

logger = logging.getLogger("OjoDeLisary")

# --- HELPER DE EXTRACCIÓN SEGURO ---
def safe_get_content(msg: Union[BaseMessage, dict, tuple]) -> str:
    """Extrae el contenido de un mensaje sin importar su formato técnico."""
    if hasattr(msg, 'content'): # Objeto LangChain
        return str(msg.content)
    if isinstance(msg, dict):   # Diccionario (Serialización API)
        return str(msg.get("content", ""))
    if isinstance(msg, (tuple, list)) and len(msg) >= 2: # Tupla antigua
        return str(msg[1])
    return str(msg)

# --- NODOS DE CONTROL ---

def router_node(state: AgentState, config: RunnableConfig):
    """
    Analiza la entrada y decide qué especialistas deben actuar.
    """
    messages = state.get("messages", [])
    
    # 1. Si ya hay agentes en la cola (viniendo de un especialista), no reclasificamos
    if state.get("selected_agents") and len(state["selected_agents"]) > 0:
        return {}

    # 2. Verificamos si el último mensaje es de un experto para evitar bucles
    if messages:
        last_msg_content = safe_get_content(messages[-1])
        expert_tags = ["[RULES_EXPERT]", "[SPELL_MENTOR]", "[CHAR_BUILDER]", "[WEB_EXPERT]", "[CHAT_EXPERT]"]
        if any(tag in last_msg_content for tag in expert_tags):
            return {"selected_agents": []}

    # 3. Clasificación inicial usando el Router
    try:
        router = DnDRouter(callbacks=config.get("callbacks", []))

        text = get_human_query(messages)

        # El router devuelve una LISTA de strings, ej: ["spells"]
        intents = router.classify_intent(text)

        logger.info(f"🔮 [RouterNode] Intenciones detectadas: {intents}")

        return {
        "selected_agents": intents
        }
    except Exception as e:
        logger.error(f"❌ Error en router_node: {e}")
        return {"selected_agents": ["chat"]}

def orchestrator(state: AgentState):
    """
    Decide el siguiente paso basado en la lista 'selected_agents'.
    """
    pending = state.get("selected_agents", [])

    if not pending or len(pending) == 0:
        return "aggregator"

    # Tomamos el primer agente y lo normalizamos
    next_agent = str(pending[0]).lower().strip()

    # Mapeo de intención a nombre de nodo (plural/singular compatible)
    mapping = {
        "spells": "spells",
        "spell": "spells",
        "rules": "rules",
        "rule": "rules",
        "builder": "builder",
        "char": "builder",
        "web": "web",
        "wiki": "web",
        "chat": "chat"
    }

    target = mapping.get(next_agent, "aggregator")
    logger.info(f"🔀 [Orchestrator] Siguiente destino: {target}")
    return target

# --- DISEÑO DEL FLUJO (WORKFLOW) ---

workflow = StateGraph(AgentState)

# 1. Registro de Nodos
workflow.add_node("router_node", router_node)
workflow.add_node("chat", chat_node)
workflow.add_node("web", web_node)
workflow.add_node("builder", builder_node)
workflow.add_node("rules", rules_node)
workflow.add_node("spells", spell_node)
workflow.add_node("aggregator", aggregator_node)

# 2. Punto de Entrada
workflow.set_entry_point("router_node")

# 3. Aristas Condicionales (Lógica de ruteo)
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

# 4. Aristas Fijas (Retorno al router o fin)
# El experto de chat suele ser conclusivo
workflow.add_edge("chat", END)

# Los expertos técnicos vuelven al router para ver si hay más tareas en la lista
workflow.add_edge("web", "router_node")
workflow.add_edge("builder", "router_node")
workflow.add_edge("rules", "router_node")
workflow.add_edge("spells", "router_node")

# El agregador sintetiza todo y cierra el ciclo
workflow.add_edge("aggregator", END)

# Compilación
agent_workflow = workflow