from langchain_community.tools.tavily_search import TavilySearchResults
from src.core.logging_config import logger
from langchain_core.runnables import RunnableConfig

class WikiTool:
    def __init__(self, k: int = 5):
        # k es el número de resultados de búsqueda que queremos
        self.search_tool = TavilySearchResults(k=k)

    def search(self, query: str, config: RunnableConfig = None) -> str:
        """
        Realiza una búsqueda web optimizada para D&D (Lore, FAQs, Sage Advice).
        """
        logger.info(f"🌐 [Tavily] Buscando en la red: {query[:50]}...")

        try:
            # Añadimos contexto de D&D a la búsqueda para evitar resultados genéricos
            enhanced_query = f"D&D 5e rules lore: {query}"

            # Ejecutamos la búsqueda pasándole los callbacks de Langfuse
            results = self.search_tool.invoke(
                {"query": enhanced_query},
                config=config
            )

            if not results:
                return "No se encontró información relevante en los planos exteriores (Web)."

            # Formateamos los resultados para el LLM
            context = "RESULTADOS DE LA WEB:\n"
            for res in results:
                context += f"\n- Fuente: {res['url']}\n  Contenido: {res['content']}\n"

            return context

        except Exception as e:
            logger.error(f"❌ [WebTool] Error en Tavily: {e}")
            return "Hubo una interferencia mágica al consultar la red."