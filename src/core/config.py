from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional

class Settings(BaseSettings):
    # --- API KEYS ---
    FIREWORKS_API_KEY: Optional[str] = None
    TAVILY_API_KEY: Optional[str] = None

    # --- RUTAS DEL PROYECTO ---
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    CHROMA_PATH: str = str(BASE_DIR / "data" / "vector_store")
    MANUALS_PATH: str = str(BASE_DIR / "data" / "manuales")

    # --- CONFIGURACIÓN DE LANGFUSE ---
    LANGFUSE_PUBLIC_KEY: Optional[str] = None
    LANGFUSE_SECRET_KEY: Optional[str] = None
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"

    # --- CONFIGURACIÓN DE MODELOS (QWEN 2.5) ---
    ROUTING_MODEL: str = "accounts/fireworks/models/qwen3-8b"
    REASONING_MODEL: str = "accounts/fireworks/models/qwen3-8b"

    # --- CONFIGURACIÓN DE PYDANTIC ---
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent.parent / ".env"),
        extra="ignore"
    )
    # --- PERSISTENCIA db ---
    # Ruta para la base de datos de hilos de LangGraph
    DB_PATH: str = str(BASE_DIR / "data" / "chat_history.db")

settings = Settings()

DB_PATH = settings.DB_PATH