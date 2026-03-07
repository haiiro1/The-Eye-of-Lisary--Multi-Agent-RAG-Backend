from langchain_community.tools import DuckDuckGoSearchRun

class WikiTool:
    def __init__(self):
        self.search_engine = DuckDuckGoSearchRun()

    def search_all_dnd(self, query: str) -> str:
        """Busca en Wikidot y Dandwiki simultáneamente."""
        return self.search_engine.run(f"{query} 5e (site:wikidot.com OR site:dandwiki.com)")

    def search_specific(self, query: str, site: str) -> str:
        """Busca solo en un sitio específico (wikidot o dandwiki)."""
        return self.search_engine.run(f"{query} 5e site:{site}.com")