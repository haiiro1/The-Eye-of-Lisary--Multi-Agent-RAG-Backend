from langchain_community.tools import DuckDuckGoSearchRun
from src.core.logging_config import logger

class WikiTool:
    def __init__(self):
        # Usamos DuckDuckGo como motor base
        self.search_engine = DuckDuckGoSearchRun()

    def search_all_dnd(self, query: str) -> str:
        """
        Busca en Wikidot y Dandwiki y etiqueta los resultados.
        """
        logger.info(f"🌐 [WikiTool] Buscando en fuentes externas: {query}")

        # Optimizamos la query para priorizar contenido de 5e
        search_query = f"{query} 5e dnd (site:wikidot.com OR site:dandwiki.com)"

        try:
            raw_results = self.search_engine.run(search_query)

            # Post-procesamiento simple para ayudar al LLM a distinguir
            if "dandwiki.com" in raw_results.lower() and "wikidot.com" in raw_results.lower():
                prefix = "[FUENTES MIXTAS DETECTADAS]\n"
            elif "dandwiki.com" in raw_results.lower():
                prefix = "[ALERTA: CONTENIDO HOMEBREW (Dandwiki)]\n"
            elif "wikidot.com" in raw_results.lower():
                prefix = "[FUENTE: WIKIDOT (Oficial/Expansiones)]\n"
            else:
                prefix = "[INFO WEB GENÉRICA]\n"

            return f"{prefix}{raw_results}"

        except Exception as e:
            logger.error(f"❌ Error en búsqueda web: {e}")
            return "No se pudo obtener información externa en este momento."

    def search_specific(self, query: str, site: str) -> str:
        """Busca solo en un sitio específico con validación de sitio."""
        valid_sites = ["wikidot", "dandwiki"]
        if site.lower() not in valid_sites:
            return f"Error: El sitio {site} no está en la lista blanca de búsqueda."

        return self.search_engine.run(f"{query} 5e site:{site}.com")