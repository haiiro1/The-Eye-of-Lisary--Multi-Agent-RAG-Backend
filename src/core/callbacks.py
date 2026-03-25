from langfuse import Langfuse
from langfuse.langchain import CallbackHandler
from src.core.config import settings #

def get_langfuse_callback(session_id: str):
    handler = CallbackHandler()
    handler.session_id = session_id
    return handler

def get_langfuse_client():
    """
    Si las variables de entorno están bien configuradas,
    no le pases argumentos. El SDK los tomará solo,
    evitando errores de compatibilidad de nombres de parámetros.
    """
    return Langfuse()