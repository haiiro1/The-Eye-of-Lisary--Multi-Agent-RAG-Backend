from src.database.vector_engine import VectorEngine

class RAGTool:
    def __init__(self, k=3):
        self.retriever = VectorEngine.get_vector_store().as_retriever(
            search_kwargs={"k": k}
        )

    def search(self, query: str):
        """Busca en los manuales de D&D 5e."""
        docs = self.retriever.get_relevant_documents(query)
        return "\n\n".join([doc.page_content for doc in docs])