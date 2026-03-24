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


from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableConfig
from functools import lru_cache

# --- HELPERS DE EXTRACCIÓN ---
@lru_cache(maxsize=1)
def get_rag_tool():
    return RAGTool(k=4)

@lru_cache(maxsize=1)
def get_wiki_tool():
    return WikiTool()

def get_human_query(messages):
    """Extrae el último mensaje del usuario para el contexto de búsqueda"""
    for msg in reversed(messages):
        role = msg.type if hasattr(msg, 'type') else (msg[0] if isinstance(msg, tuple) else "")
        content = msg.content if hasattr(msg, 'content') else (msg[1] if isinstance(msg, tuple) else str(msg))
        if role == "human":
            return str(content).replace("surje", "surge").strip()
    return "Consulta general de D&D"

def debe_buscar_en_rag(query: str) -> bool:
    """Determina si la consulta requiere una búsqueda técnica en los manuales"""
    terminos_tecnicos = [
        "regla", "ataque", "daño", "hechizo", "conjuro", "clase", "nivel",
        "dote", "bonificador", "tirada", "salvación", "clase de armadura",
        "espacio de conjuro", "acción", "reacción"
    ]
    query_lower = query.lower()

    tiene_termino = any(t in query_lower for t in terminos_tecnicos)
    es_larga = len(query.split()) > 5
    menciona_ca = re.search(r'\bca\b', query_lower)

    return tiene_termino or es_larga or menciona_ca

def _pop_agent(state: AgentState):
    """Actualiza la cola de agentes pendientes"""
    pending = state.get("selected_agents", [])
    return pending[1:] if len(pending) > 1 else []

# --- NODOS ESPECIALISTAS ---

def chat_node(state: AgentState, config: RunnableConfig):
    session_id = config["configurable"].get("thread_id", "default_session")
    query = get_human_query(state["messages"])
    expert = ChatExpert(session_id=session_id, chat_history=state["messages"], callbacks=config.get("callbacks", []))
    result = expert.run(user_input=query, language=state.get("language", "es"), config=config)
    return {"messages": [AIMessage(content=f"[CHAT_EXPERT]: {result['answer']}")], "selected_agents": _pop_agent(state)}

def rules_node(state: AgentState, config: RunnableConfig):
    session_id = config["configurable"].get("thread_id", "default_session")
    query = get_human_query(state["messages"])
    # Búsqueda RAG condicionada a la naturaleza de la consulta
    context = get_rag_tool().search(f"Regla: {query}") if debe_buscar_en_rag(query) else ""
    expert = RulesExpert(session_id=session_id, chat_history=state["messages"], callbacks=config.get("callbacks", []))
    result = expert.run(user_input=query, language=state.get("language", "es"), extra_info=context, config=config)
    return {"messages": [AIMessage(content=f"[RULES_EXPERT]: {result['answer']}")], "selected_agents": _pop_agent(state)}

def spell_node(state: AgentState, config: RunnableConfig):
    session_id = config["configurable"].get("thread_id", "default_session")
    query = get_human_query(state["messages"])
    # Búsqueda RAG condicionada para optimizar latencia
    context = get_rag_tool().search(f"Hechizo: {query}") if debe_buscar_en_rag(query) else ""
    expert = SpellMentor(session_id=session_id, chat_history=state["messages"], callbacks=config.get("callbacks", []))
    result = expert.run(user_input=query, language=state.get("language", "es"), extra_info=context, config=config)
    return {"messages": [AIMessage(content=f"[SPELL_MENTOR]: {result['answer']}")], "selected_agents": _pop_agent(state)}

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
    expert = WebOmniExpert(session_id=session_id, chat_history=state["messages"], callbacks=config.get("callbacks", []))
    result = expert.run(user_input=query, language=state.get("language", "es"), extra_info=context, config=config)
    return {"messages": [AIMessage(content=f"[WEB_EXPERT]: {result['answer']}")], "selected_agents": _pop_agent(state)}

# --- NODO FINAL: AGREGADOR ---

def aggregator_node(state: AgentState, config: RunnableConfig):
    try:
        llm = LLMFactory.get_model(is_reasoning=False, callbacks=config.get("callbacks", []))
        user_query = get_human_query(state["messages"])
        lang = state.get("language", "es")

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
        response = chain.invoke({"clean_history": "\n".join(clean_history), "user_query": user_query, "idioma": lang}, config=config)

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
