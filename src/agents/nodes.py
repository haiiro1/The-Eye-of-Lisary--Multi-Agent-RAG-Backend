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

# Inicialización única de herramientas gestionadas por el orquestador
rag_tool = RAGTool(k=3)
wiki_tool = WikiTool()
sheet_manager = SheetManager()

def _get_text(message):
    if isinstance(message, tuple): return message[1]
    if hasattr(message, 'content'): return message.content
    return str(message)

# --- NODO: CONSTRUCCIÓN/FICHAS ---
def builder_node(state: AgentState):
    user_input = _get_text(state["messages"][-1])

    # 1. El orquestador prepara el contexto
    manual_context = rag_tool.search(user_input)
    sheet_context = state.get("sheet_context", "Ficha no disponible")
    combined_info = f"MANUALES:\n{manual_context}\n\nESTADO FICHA:\n{sheet_context}"

    # 2. El agente procesa la información
    expert = CharBuilder(session_id="lg_session", chat_history=state["messages"])
    result = expert.run(
        user_input=user_input,
        language=state.get("language", "es"),
        extra_info=combined_info
    )

    return {"messages": [("assistant", f"[CHAR_BUILDER]: {result['answer']}")]}

# --- NODO: HECHIZOS ---
def spell_node(state: AgentState):
    user_input = _get_text(state["messages"][-1])

    # Buscamos específicamente hechizos en el RAG
    spell_info = rag_tool.search(f"Hechizos: {user_input}")

    expert = SpellMentor(session_id="lg_session", chat_history=state["messages"])
    result = expert.run(
        user_input=user_input,
        language=state.get("language", "es"),
        extra_info=spell_info
    )

    return {"messages": [("assistant", f"[SPELL_MENTOR]: {result['answer']}")]}

# --- NODO: REGLAS ---
def rules_node(state: AgentState):
    user_input = _get_text(state["messages"][-1])

    # Buscamos la regla técnica
    rule_info = rag_tool.search(f"Regla oficial: {user_input}")

    expert = RulesExpert(session_id="lg_session", chat_history=state["messages"])
    result = expert.run(
        user_input=user_input,
        language=state.get("language", "es"),
        extra_info=rule_info
    )

    return {"messages": [("assistant", f"[RULES_EXPERT]: {result['answer']}")]}

# --- NODO: WEB (Filtro de respaldo/Wiki) ---
def web_node(state: AgentState):
    user_input = _get_text(state["messages"][-1])

    # El orquestador busca en la Wiki
    web_info = wiki_tool.search(user_input)

    expert = WebOmniExpert(session_id="lg_session", chat_history=state["messages"])
    result = expert.run(
        user_input=user_input,
        language=state.get("language", "es"),
        extra_info=web_info
    )

    return {"messages": [("assistant", f"[WEB_EXPERT]: {result['answer']}")]}

# --- NODO: AGREGADOR (Unificador de respuestas) ---
def aggregator_node(state: AgentState):
    llm = LLMFactory.get_model(is_reasoning=False)

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
    unified_answer = chain.invoke({
        "messages": state["messages"],
        "language": state.get("language", "es")
    })

    return {
        "messages": [("assistant", unified_answer)],
        "selected_agents": [] # Limpiamos la cola
    }