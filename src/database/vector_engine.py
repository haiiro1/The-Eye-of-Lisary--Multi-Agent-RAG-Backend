import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from src.core.config import settings

class VectorEngine:
    @staticmethod
    def get_embedding_model():
        return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    @classmethod
    def get_vector_store(cls):
        if not os.path.exists(settings.CHROMA_PATH):
            os.makedirs(settings.CHROMA_PATH, exist_ok=True)

        return Chroma(
            persist_directory=settings.CHROMA_PATH,
            embedding_function=cls.get_embedding_model()
        )