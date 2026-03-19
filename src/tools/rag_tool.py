import re
from src.database.vector_engine import VectorEngine
from src.core.logging_config import logger

class RAGTool:
    def __init__(self, k: int = 3):
        self.vector_store = VectorEngine.get_vector_store()
        self.k = k

    def _clean_query(self, query: str) -> str:
        """
        Limpia la consulta para evitar que el RAG busque pensamientos
        internos de la IA o etiquetas técnicas.
        """
        # 1. Eliminar bloques <think>...</think>
        query = re.sub(r'<think>.*?</think>', '', query, flags=re.DOTALL)
        # 2. Eliminar prefijos de agentes como [RULES_EXPERT]:
        query = re.sub(r'\[.*?\]:', '', query)
        return query.strip()

    def search(self, query: str, config: dict = None) -> str:
        """
        Busca en los manuales de D&D.
        Nota: Eliminamos 'config' de la llamada a la DB para evitar errores.
        """
        cleaned_query = self._clean_query(query)

        # Solo logueamos los primeros 100 caracteres para no ensuciar el log
        logger.info(f"🔍 [RAGTool] Buscando en manuales: {cleaned_query[:100]}...")

        try:
            # IMPORTANTE: Aquí NO pasamos ni callbacks ni config.
            # ChromaDB solo acepta la query y el número de resultados.
            results = self.vector_store.similarity_search(
                cleaned_query,
                k=self.k
            )

            if not results:
                return "No se encontró información específica en los manuales oficiales."

            # Unificamos el contenido de los fragmentos encontrados
            context = "\n\n".join([doc.page_content for doc in results])
            return context

        except Exception as e:
            logger.error(f"❌ [RAGTool] Error en la búsqueda vectorial: {e}")
            return "Error al consultar los manuales de reglas."