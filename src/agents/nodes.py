import re
from src.agents.char_builder import CharBuilder
from src.agents.chat_expert import ChatExpert
from src.agents.rules_expert import RulesExpert
from src.agents.web_omni_expert import WebOmniExpert
from src.agents.spell_mentor import SpellMentor
from src.core.factory import LLMFactory
from src.core.state import AgentState
from src.tools.rag_tool import RAGTool
from src.tools.wiki_tool import WikiTool
from src.core.logging_config import logger


# Importaciones nativas de LangChain para compatibilidad total con el Grafo
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableConfig
from functools import lru_cache

# --- HELPERS DE EXTRACCIÓN ---
@lru_cache(maxsize=1)
def get_rag_tool():
    return RAGTool(k=5)

@lru_cache(maxsize=1)
def get_wiki_tool():
    return WikiTool()

def get_human_query(messages):
    """Busca el último mensaje enviado por el humano para evitar buscar pensamientos de IA."""
    for msg in reversed(messages):
        # Manejo compatible con BaseMessage de LangChain y tuplas antiguas
        role = msg.type if hasattr(msg, 'type') else (msg[0] if isinstance(msg, tuple) else "")
        content = msg.content if hasattr(msg, 'content') else (msg[1] if isinstance(msg, tuple) else str(msg))

        if role == "human":
            return str(content).replace("surje", "surge").strip()
    return "Consulta general de D&D"

def _pop_agent(state: AgentState):
    """Elimina al agente actual de la cola usando la lógica de reemplazo del state."""
    pending = state.get("selected_agents", [])
    return pending[1:] if len(pending) > 1 else []

# --- NODOS ESPECIALISTAS ---

def chat_node(state: AgentState, config: RunnableConfig):
    session_id = config["configurable"].get("thread_id", "default_session")
    query = get_human_query(state["messages"])

    expert = ChatExpert(
        session_id=session_id,
        chat_history=state["messages"],
        callbacks=config.get("callbacks", [])
    )

    result = expert.run(user_input=query, language=state.get("language", "es"), config=config)

    return {
        "messages": [AIMessage(content=f"[CHAT_EXPERT]: {result['answer']}")],
        "selected_agents": _pop_agent(state)
    }

def rules_node(state: AgentState, config: RunnableConfig):
    session_id = config["configurable"].get("thread_id", "default_session")
    query = get_human_query(state["messages"])
    context = get_rag_tool().search(f"Regla: {query}")

    # Se fuerzan los nombres de los argumentos para que Python no se confunda de posición
    expert = RulesExpert(
        session_id=session_id,
        chat_history=state["messages"],
        callbacks=config.get("callbacks", [])
    )

    result = expert.run(user_input=query, language=state.get("language", "es"), extra_info=context, config=config)

    return {
        "messages": [AIMessage(content=f"[RULES_EXPERT]: {result['answer']}")],
        "selected_agents": _pop_agent(state)
    }

def spell_node(state: AgentState, config: RunnableConfig):
    session_id = config["configurable"].get("thread_id", "default_session")
    query = get_human_query(state["messages"])
    context = get_rag_tool().search(f"Hechizo: {query}")

    expert = SpellMentor(
        session_id=session_id,
        chat_history=state["messages"],
        callbacks=config.get("callbacks", [])
    )

    result = expert.run(user_input=query, language=state.get("language", "es"), extra_info=context, config=config)

    return {
        "messages": [AIMessage(content=f"[SPELL_MENTOR]: {result['answer']}")],
        "selected_agents": _pop_agent(state)
    }

def builder_node(state: AgentState, config: RunnableConfig):
    session_id = config["configurable"].get("thread_id", "default_session")
    query = get_human_query(state["messages"])


    rag_context = get_rag_tool().search(f"Creación/Mejora: {query}")


    sheet_info = state.get("sheet_context", "No hay ficha vinculada.")

    full_context = str(rag_context) + "\n\nDATOS_FICHA:\n" + str(sheet_info)

    expert = CharBuilder(
        session_id=session_id,
        chat_history=state["messages"],
        callbacks=config.get("callbacks", [])
    )

    result = expert.run(
        user_input=query,
        language=state.get("language", "es"),
        extra_info=full_context,
        config=config
    )

    return {
        "messages": [AIMessage(content=f"[CHAR_BUILDER]: {result['answer']}")],
        "selected_agents": _pop_agent(state)
    }

def web_node(state: AgentState, config: RunnableConfig):

    session_id = config["configurable"].get("thread_id", "default_session")

    query = get_human_query(state["messages"])

    context = get_wiki_tool().search(query, config=config)

    expert = WebOmniExpert(
        session_id=session_id,
        chat_history=state["messages"],
        callbacks=config.get("callbacks", [])
    )

    result = expert.run(
        user_input=query,
        language=state.get("language", "es"),
        extra_info=context,
        config=config
    )

    return {
        "messages": [AIMessage(content=f"[WEB_EXPERT]: {result['answer']}")],
        "selected_agents": _pop_agent(state)
    }

# --- NODO FINAL: AGREGADOR ---

def aggregator_node(state: AgentState, config: RunnableConfig):
    try:
        llm = LLMFactory.get_model(is_reasoning=False, callbacks=config.get("callbacks", []))
        user_query = get_human_query(state["messages"])

        # Recuperamos el idioma detectado originalmente por el sistema como respaldo
        fallback_lang = state.get("language", "es")

        clean_history = []
        for msg in state["messages"]:
            # ... (tu lógica de limpieza <think> está perfecta)
            content = msg.content if hasattr(msg, 'content') else str(msg)
            # SUGERENCIA: Eliminar también los prefijos [AGENT_NAME] para que el agregador 
            # no crea que debe hablar de forma técnica.
            clean_content = re.sub(r'\[.*?\]:', '', content).strip()
            if clean_content: clean_history.append(clean_content)

        prompt = ChatPromptTemplate.from_template("""
            Eres el Ojo de Lisary, un oráculo místico de D&D 5e.
            Redacta una respuesta coherente y mística usando las visiones de tus especialistas.
            NO uses etiquetas <think>.

            REGLA DE ORO:
            Responde en el idioma de la pregunta. Si no estás seguro, usa: {idioma_respaldo}.

            VISIONES:
            {clean_history}

            PREGUNTA:
            {user_query}

            RESPUESTA DEL ORÁCULO:
        """)

        chain = prompt | llm | StrOutputParser()

        # Invocamos pasando el idioma de respaldo
        response = chain.invoke({
            "clean_history": "\n".join(clean_history),
            "user_query": user_query,
            "idioma_respaldo": fallback_lang
        }, config=config)

        # Limpieza final por seguridad
        final_response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()

        return {"messages": [AIMessage(content=final_response)], "selected_agents": []}
    except Exception as e:
        logger.error(f"Error en agregador: {e}")
        return {"messages": [AIMessage(content="El Ojo está nublado...")], "selected_agents": []}