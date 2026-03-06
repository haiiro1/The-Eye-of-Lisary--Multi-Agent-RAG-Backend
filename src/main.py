# src/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import os

class Settings(BaseSettings):
    # API Keys
    FIREWORKS_API_KEY: str
    TAVILY_API_KEY: str

    # Rutas (Calculadas automáticamente desde la raíz del proyecto)
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    CHROMA_PATH: str = str(BASE_DIR / "data" / "vector_store")
    MANUALS_PATH: str = str(BASE_DIR / "data" / "manuales")

    # Modelos
    ROUTING_MODEL: str
    REASONING_MODEL: str

    # Vincular con el archivo .env
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent.parent / ".env"),
        extra="ignore"
    )

# Instancia global
settings = Settings()