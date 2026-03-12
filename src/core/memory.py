import os
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langchain_community.chat_message_histories import SQLChatMessageHistory

def get_graph_checkpointer():
    """Configura el Checkpointer ASÍNCRONO para LangGraph usando aiosqlite."""
    db_path = "data/chat_history.db"
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return AsyncSqliteSaver.from_conn_string(db_path)

def get_chat_history(session_id: str):
    """Recupera el historial de mensajes de forma independiente."""
    return SQLChatMessageHistory(
        session_id=session_id,
        connection="sqlite:///data/chat_history.db"
    )