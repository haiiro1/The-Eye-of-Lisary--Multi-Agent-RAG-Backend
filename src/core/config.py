from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional

class Settings(BaseSettings):
    # --- API KEYS ---
    # Al poner Optional y None, el editor deja de marcar error si el .env no se ha leído aún
    FIREWORKS_API_KEY: Optional[str] = None
    TAVILY_API_KEY: Optional[str] = None

    # --- RUTAS DEL PROYECTO ---
    # Calculamos la raíz del proyecto (3 niveles arriba de este archivo)
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    CHROMA_PATH: str = str(BASE_DIR / "data" / "vector_store")
    MANUALS_PATH: str = str(BASE_DIR / "data" / "manuales")

    # --- CONFIGURACIÓN DE MODELOS (QWEN 2.5) ---
    ROUTING_MODEL: str = "accounts/fireworks/models/qwen2p5-72b-instruct"
    REASONING_MODEL: str = "accounts/fireworks/models/qwen2p5-72b-instruct"

    # --- CONFIGURACIÓN DE PYDANTIC ---
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent.parent / ".env"),
        extra="ignore"
    )

# Instancia global que importarán todos los demás módulos
settings = Settings()