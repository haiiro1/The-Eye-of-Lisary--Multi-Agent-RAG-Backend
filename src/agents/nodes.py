from src.agents.char_builder import CharBuilder
from src.agents.rules_expert import RulesExpert
from src.agents.web_omni_expert import WebOmniExpert
from src.agents.spell_mentor import SpellMentor
from src.core.factory import LLMFactory
from src.core.state import AgentState
from src.tools.rag_tool import RAGTool
from src.tools.wiki_tool import WikiTool
from src.tools.sheet_manager import SheetManager
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableConfig

# Inicialización de herramientas
rag_tool = RAGTool(k=3)
wiki_tool = WikiTool()
sheet_manager = SheetManager()

def _get_text(message):
    if isinstance(message, tuple): return message[1]
    if hasattr(message, 'content'): return message.content
    return str(message)

# --- NODO: CONSTRUCCIÓN/FICHAS ---
def builder_node(state: AgentState, config: RunnableConfig):
    # Extraemos callbacks y session_id (thread_id) del config
    callbacks = config.get("callbacks", [])
    session_id = config["configurable"].get("thread_id", "default_session")

    user_input = _get_text(state["messages"][-1])
    manual_context = rag_tool.search(user_input)
    sheet_context = state.get("sheet_context", "Ficha no disponible")
    combined_info = f"MANUALES:\n{manual_context}\n\nESTADO FICHA:\n{sheet_context}"

    # Inyectamos los callbacks al agente
    expert = CharBuilder(session_id=session_id, chat_history=state["messages"], callbacks=callbacks)
    result = expert.run(
        user_input=user_input,
        language=state.get("language", "es"),
        extra_info=combined_info
    )

    return {"messages": [("assistant", f"[CHAR_BUILDER]: {result['answer']}")]}

# --- NODO: HECHIZOS ---
def spell_node(state: AgentState, config: RunnableConfig):
    callbacks = config.get("callbacks", [])
    session_id = config["configurable"].get("thread_id", "default_session")

    user_input = _get_text(state["messages"][-1])
    spell_info = rag_tool.search(f"Hechizos: {user_input}")

    expert = SpellMentor(session_id=session_id, chat_history=state["messages"], callbacks=callbacks)
    result = expert.run(
        user_input=user_input,
        language=state.get("language", "es"),
        extra_info=spell_info
    )

    return {"messages": [("assistant", f"[SPELL_MENTOR]: {result['answer']}")]}

# --- NODO: REGLAS ---
def rules_node(state: AgentState, config: RunnableConfig):
    callbacks = config.get("callbacks", [])
    session_id = config["configurable"].get("thread_id", "default_session")

    user_input = _get_text(state["messages"][-1])
    rule_info = rag_tool.search(f"Regla oficial: {user_input}")

    expert = RulesExpert(session_id=session_id, chat_history=state["messages"], callbacks=callbacks)
    result = expert.run(
        user_input=user_input,
        language=state.get("language", "es"),
        extra_info=rule_info
    )

    return {"messages": [("assistant", f"[RULES_EXPERT]: {result['answer']}")]}

# --- NODO: WEB ---
def web_node(state: AgentState, config: RunnableConfig):
    callbacks = config.get("callbacks", [])
    session_id = config["configurable"].get("thread_id", "default_session")

    user_input = _get_text(state["messages"][-1])
    web_info = wiki_tool.search(user_input)

    expert = WebOmniExpert(session_id=session_id, chat_history=state["messages"], callbacks=callbacks)
    result = expert.run(
        user_input=user_input,
        language=state.get("language", "es"),
        extra_info=web_info
    )

    return {"messages": [("assistant", f"[WEB_EXPERT]: {result['answer']}")]}

# --- NODO: AGREGADOR ---
def aggregator_node(state: AgentState, config: RunnableConfig):
    # El agregador también debe reportar sus métricas a Langfuse
    callbacks = config.get("callbacks", [])
    llm = LLMFactory.get_model(is_reasoning=False, callbacks=callbacks)

    prompt = ChatPromptTemplate.from_template("""
        Eres el 'Ojo de Lisary', guía místico de D&D 5e.
        Tu misión es unificar las visiones de tus especialistas en una sola respuesta coherente y fluida.

        INSTRUCCIONES:
        1. Elimina etiquetas técnicas como [CHAR_BUILDER], [SPELL_MENTOR], etc.
        2. No menciones que consultaste a especialistas.
        3. Si hay consejos de construcción y de hechizos, únelos narrativamente.
        4. Responde en {language}.

        VISIONES RECIBIDAS:
        {messages}
    """)

    chain = prompt | llm | StrOutputParser()
    # Pasamos el config (que contiene los callbacks) a invoke
    unified_answer = chain.invoke({
        "messages": state["messages"],
        "language": state.get("language", "es")
    }, config=config)

    return {
        "messages": [("assistant", unified_answer)],
        "selected_agents": []
    }