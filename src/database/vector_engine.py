import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from src.core.config import settings

class VectorEngine:
    # Variable de clase para cachear el modelo y no recargarlo en cada nodo
    _embedding_model = None

    @classmethod
    def get_embedding_model(cls):
        """Carga y devuelve el modelo de embeddings con cacheo."""
        if cls._embedding_model is None:
            # all-MiniLM-L6-v2 es eficiente para CPU
            cls._embedding_model = HuggingFaceEmbeddings(
                model_name="all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'}
            )
        return cls._embedding_model

    @classmethod
    def get_vector_store(cls):
        """
        Configura y devuelve la conexión persistente a ChromaDB.
        Definimos explícitamente la métrica de distancia.
        'cosine' es superior para embeddings de texto que 'l2'.
        que mide?: l2 Mide la distancia en línea recta entre los puntos finales de los vectores.
        """
        if not os.path.exists(settings.CHROMA_PATH):
            os.makedirs(settings.CHROMA_PATH, exist_ok=True)

        return Chroma(
            persist_directory=settings.CHROMA_PATH,
            embedding_function=cls.get_embedding_model(),
            collection_metadata={"hnsw:space": "cosine"}
        )