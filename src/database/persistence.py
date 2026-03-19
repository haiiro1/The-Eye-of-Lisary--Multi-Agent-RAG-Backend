import os
from contextlib import asynccontextmanager
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langchain_community.chat_message_histories import SQLChatMessageHistory
from src.core.config import settings

@asynccontextmanager
async def get_graph_checkpointer():
    clean_path = settings.DB_PATH.replace("sqlite:///", "")
    # Asegurar que el directorio existe para Docker
    os.makedirs(os.path.dirname(clean_path), exist_ok=True)

    # El 'async with' es obligatorio en las versiones nuevas
    async with AsyncSqliteSaver.from_conn_string(clean_path) as saver:
        yield saver

def get_chat_history(session_id: str):
    """Historial de mensajes compatible con SQLAlchemy."""
    clean_path = settings.DB_PATH.replace("sqlite:///", "")
    return SQLChatMessageHistory(
        session_id=session_id,
        connection=f"sqlite:///{clean_path}"
    )