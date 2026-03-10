from src.database.vector_engine import VectorEngine
from langchain_core.documents import Document
from typing import List
from src.core.logging_config import logger

class RAGTool:
    def __init__(self, k=5):
        # Aumentamos k a 5 para asegurar que el SpellMentor tenga suficiente contexto
        self.vector_store = VectorEngine.get_vector_store()
        self.k = k

    def search(self, query: str) -> str:
        """
        Busca en los manuales de D&D 5e y devuelve el texto formateado.
        """
        try:
            logger.info(f"🔍 [RAGTool] Consultando manuales por: '{query}'")
            
            # Realizamos la búsqueda de similitud simple (sin filtros para evitar errores de llave)
            docs = self.vector_store.similarity_search(query, k=self.k)

            if not docs:
                return "No se encontró información oficial en los manuales sobre este tema."

            # Validación de integridad: Si el primer doc es solo 1 letra, alertamos
            if len(docs[0].page_content) <= 1:
                logger.error("🚨 [RAGTool] ¡PELIGRO! Los datos en la DB siguen siendo letras sueltas.")
                return "Error: La base de datos de manuales está corrupta (fragmentos de 1 caracter)."

            return self._format_results(docs)
            
        except Exception as e:
            logger.error(f"❌ [RAGTool] Error en la búsqueda: {e}")
            return f"Error técnico al consultar los manuales: {e}"

    def _format_results(self, docs: List[Document]) -> str:
        """Formatea los resultados uniendo los fragmentos correctamente."""
        formatted_parts = []
        for i, doc in enumerate(docs, 1):
            # Usamos .get("source") para que coincida con lo que pusimos en ingesta.py
            source = doc.metadata.get("source", "Manual de D&D")
            page = doc.metadata.get("page", "?")
            
            # Limpiamos el contenido por si acaso trae saltos de línea extraños
            content = doc.page_content.strip()
            
            block = f"--- FUENTE {i} [{source} - Pág. {page}] ---\n{content}"
            formatted_parts.append(block)

        return "\n\n".join(formatted_parts)