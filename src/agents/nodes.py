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
from src.core.callbacks import get_langfuse_client


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
    """Busca el último mensaje del humano de forma segura para evitar errores de índices."""
    for msg in reversed(messages):
        role = ""
        content = ""

        # 1. Caso: Objeto de LangChain (HumanMessage, AIMessage)
        if hasattr(msg, 'type'):
            role = msg.type
            content = msg.content
        # 2. Caso: Diccionario (Aquí es donde fallaba tu código)
        elif isinstance(msg, dict):
            role = msg.get("type") or msg.get("role", "")
            content = msg.get("content", "")
        # 3. Caso: Tupla antigua ("human", "hola")
        elif isinstance(msg, (tuple, list)) and len(msg) >= 2:
            role = msg[0]
            content = msg[1]

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
    context = get_rag_tool().search(query)

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
        client = get_langfuse_client()
        prompt_res = client.get_prompt("dnd-aggregator")

        llm = LLMFactory.get_model(is_reasoning=False, callbacks=config.get("callbacks", []))
        user_query = get_human_query(state["messages"])
        fallback_lang = state.get("language", "es")

        clean_history = []
        # Error corregido: iterar sobre objetos de mensaje de forma segura
        for msg in state["messages"]:
            # Extraemos el contenido sin importar si es objeto o dict
            if hasattr(msg, 'content'):
                content = msg.content
            elif isinstance(msg, dict):
                content = msg.get("content", "")
            else:
                content = str(msg)

            # Limpieza de ruido técnico
            content_clean = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
            content_clean = re.sub(r'\[.*?\]:', '', content_clean).strip()

            # Solo agregamos si no es la pregunta original y tiene contenido
            if content_clean and content_clean not in user_query:
                clean_history.append(content_clean)

        prompt_tpl = ChatPromptTemplate.from_template(prompt_res.get_langchain_prompt())
        chain = prompt_tpl | llm | StrOutputParser()

        response = chain.invoke({
            "clean_history": "\n".join(clean_history),
            "user_query": user_query,
            "idioma_respaldo": fallback_lang
        }, config=config)

        final_response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()

        return {"messages": [AIMessage(content=final_response)], "selected_agents": []}

    except Exception as e:
        logger.error(f"❌ Error en agregador: {e}")
        return {"messages": [AIMessage(content="El Ojo está nublado... (Error de índices)")], "selected_agents": []}