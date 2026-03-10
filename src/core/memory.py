import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_community.chat_message_histories import SQLChatMessageHistory

def get_graph_checkpointer():
    """
    Configura el ahorrador de puntos de control (Checkpointer) para LangGraph.
    Permite que el grafo sea persistente y recupere estados anteriores.
    """
    # Establecemos conexión con la base de datos definida en el proyecto
    # check_same_thread=False es necesario para aplicaciones FastAPI/Uvicorn
    conn = sqlite3.connect("data/chat_history.db", check_same_thread=False)
    return SqliteSaver(conn)

def get_chat_history(session_id: str):
    """
    Mantiene compatibilidad para recuperar el historial de mensajes 
    de forma independiente si es necesario.
    """
    return SQLChatMessageHistory(
        session_id=session_id,
        connection="sqlite:///data/chat_history.db"
    )