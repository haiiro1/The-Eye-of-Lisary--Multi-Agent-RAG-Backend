import re
from src.agents.char_builder import CharBuilder
from src.agents.rules_expert import RulesExpert
from src.agents.web_omni_expert import WebOmniExpert
from src.agents.spell_mentor import SpellMentor
from src.core.factory import LLMFactory
from src.core.state import AgentState
from src.tools.rag_tool import RAGTool
from src.tools.wiki_tool import WikiTool

# Importaciones nativas de LangChain para compatibilidad total con el Grafo
from langchain_core.messages import AIMessage, HumanMessage
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
            # Pequeña corrección de términos comunes para mejorar el RAG
            return str(content).replace("surje", "surge").strip()
    return "Consulta general de D&D"

def _pop_agent(state: AgentState):
    """Elimina al agente actual de la cola usando la lógica de reemplazo del state."""
    pending = state.get("selected_agents", [])
    return pending[1:] if len(pending) > 1 else []

# --- NODOS ESPECIALISTAS ---

def rules_node(state: AgentState, config: RunnableConfig):
    session_id = config["configurable"].get("thread_id", "default_session")
    query = get_human_query(state["messages"])
    context = get_rag_tool().search(f"Regla: {query}")

    # Forzamos los nombres de los argumentos para que Python no se confunda de posición
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
    context = get_rag_tool().search(f"Creación/Mejora: {query}")

    expert = CharBuilder(
        session_id=session_id,
        chat_history=state["messages"],
        callbacks=config.get("callbacks", [])
    )

    result = expert.run(user_input=query, language=state.get("language", "es"), extra_info=context, config=config)

    return {
        "messages": [AIMessage(content=f"[CHAR_BUILDER]: {result['answer']}")],
        "selected_agents": _pop_agent(state)
    }

def web_node(state: AgentState, config: RunnableConfig):
    # 1. Extraemos el session_id (thread_id) de la configuración
    session_id = config["configurable"].get("thread_id", "default_session")

    query = get_human_query(state["messages"])

    # 2. Tavily hace su magia
    context = get_wiki_tool().search(query, config=config)

    # 3. 🎯 EL ARREGLO: Añadimos session_id y chat_history al instanciar
    expert = WebOmniExpert(
        session_id=session_id, # <--- ¡Esto es lo que faltaba!
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
        # 1. Usamos un modelo "Instruct" (Llama 3 o similar) para que obedezca el idioma
        llm = LLMFactory.get_model(is_reasoning=False, callbacks=config.get("callbacks", []))

        # 2. Detectamos el idioma del último mensaje HUMANO
        # Esto asegura que si el usuario cambió de idioma a mitad del chat, el Ojo se adapte.
        user_query = get_human_query(state["messages"])

        # 3. Limpiamos el historial de los "pensamientos" ingleses de los expertos
        clean_history = []
        for msg in state["messages"]:
            content = msg.content if hasattr(msg, 'content') else str(msg)
            # Eliminamos los bloques <think> para que no contaminen el idioma final
            clean_content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
            if clean_content:
                clean_history.append(clean_content)

        prompt = ChatPromptTemplate.from_template("""
            Eres el Ojo de Lisary, un oráculo místico de D&D 5e.
            Tu misión es redactar la respuesta final basada en las visiones de tus especialistas.

            REGLAS CRÍTICAS DE IDIOMA:
            - Debes responder estrictamente en el MISMO IDIOMA que el usuario utilizó en su pregunta.
            - Si el usuario preguntó en español, responde en español.
            - Si el usuario preguntó en inglés, responde en inglés.
            - NO uses etiquetas <think>.
            - Mantén el tono místico y usa negritas para términos de reglas.

            HISTORIAL LIMPIO DE VISIONES:
            {clean_history}

            PREGUNTA ORIGINAL DEL USUARIO:
            {user_query}

            RESPUESTA FINAL (En el idioma del usuario):
        """)

        chain = prompt | llm | StrOutputParser()

        response = chain.invoke({
            "clean_history": "\n".join(clean_history),
            "user_query": user_query
        }, config=config)

        return {
            "messages": [AIMessage(content=response)],
            "selected_agents": []
        }
    except Exception as e:
        # Fallback por si el error de OpenTelemetry o de tokens persiste
        return {"messages": [AIMessage(content="El Ojo está nublado. Intenta preguntar de nuevo.")], "selected_agents": []}