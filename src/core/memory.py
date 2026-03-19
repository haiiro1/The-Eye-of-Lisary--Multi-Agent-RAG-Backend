import os
import logging
from contextlib import asynccontextmanager
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langchain_community.chat_message_histories import SQLChatMessageHistory
from src.core.config import DB_PATH

logger = logging.getLogger(__name__)

@asynccontextmanager
async def get_graph_checkpointer():
    """
    Checkpointer asíncrono compatible con Docker y LangGraph v0.2+
    """
    # 1. Normalizar ruta: Docker prefiere rutas absolutas o relativas al WORKDIR
    # Si DB_PATH es 'data/chat_history.db', se guardará en /app/data/...
    clean_path = DB_PATH.replace("sqlite:///", "")

    # 2. Asegurar que el directorio existe (evita errores de 'Unable to open DB')
    db_dir = os.path.dirname(clean_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    try:
        # 3. El 'async with' inicializa la conexión y crea las tablas de LangGraph
        async with AsyncSqliteSaver.from_conn_string(clean_path) as saver:
            yield saver
    except Exception as e:
        logger.error(f"Error en AsyncSqliteSaver: {e}")
        raise

def get_chat_history(session_id: str):
    """
    Historial de mensajes para LangChain.
    """
    clean_path = DB_PATH.replace("sqlite:///", "")
    # SQLAlchemy requiere obligatoriamente el prefijo sqlite:///
    connection_uri = f"sqlite:///{clean_path}"

    return SQLChatMessageHistory(
        session_id=session_id,
        connection=connection_uri
    )