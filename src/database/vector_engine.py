import os
from langchain_fireworks import FireworksEmbeddings # <--- Cambiamos esto
from langchain_chroma import Chroma
from src.core.config import settings

class VectorEngine:
    _embedding_model = None

    @classmethod
    def get_embedding_model(cls):
        """Carga el modelo de Fireworks (Ejecución en la nube, 0ms de carga local)."""
        if cls._embedding_model is None:
            # Usamos el modelo de Nomic en Fireworks (muy potente y barato)
            cls._embedding_model = FireworksEmbeddings(
                model="nomic-ai/nomic-embed-text-v1.5",
                fireworks_api_key=settings.FIREWORKS_API_KEY
            )
        return cls._embedding_model

    @classmethod
    def get_vector_store(cls):
        if not os.path.exists(settings.CHROMA_PATH):
            os.makedirs(settings.CHROMA_PATH, exist_ok=True)

        return Chroma(
            persist_directory=settings.CHROMA_PATH,
            embedding_function=cls.get_embedding_model(),
            collection_metadata={"hnsw:space": "cosine"}
        )