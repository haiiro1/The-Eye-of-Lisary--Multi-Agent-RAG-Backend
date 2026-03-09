from src.core.base_agent import BaseDnDAgent
from src.tools.wiki_tool import WikiTool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

class WebOmniExpert(BaseDnDAgent):
    def _setup_tools(self):
        return WikiTool()

    def run(self, user_input: str, language: str = "es") -> dict:
        # Buscamos en ambos sitios simultáneamente usando tu WikiTool
        web_results = self.tools.search_all_dnd(user_input)

        prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres el Cronista Omnisciente de la Red.
             Tu trabajo es filtrar y organizar información externa de D&D 5e.

             REGLAS DE FILTRADO:
             1. CLASIFICACIÓN: Identifica claramente si la fuente es 'WIKIDOT' (Contenido Oficial/Expansiones) o 'DANDWIKI' (Homebrew/Fan-made).
             2. ADVERTENCIA HOMEBREW: Si presentas datos de Dandwiki, añade siempre una nota sobre el posible desbalanceo mecánico.
             3. IDIOMA: Responde en {lang}.
             4. COMPARACIÓN: Si el usuario pregunta por algo que existe en ambas fuentes, destaca las diferencias."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "RESULTADOS DE BÚSQUEDA:\n{context}\n\nPREGUNTA: {question}")
        ])

        chain = prompt | self.llm | StrOutputParser()
        answer = chain.invoke({
            "context": web_results,
            "question": user_input,
            "lang": language,
            "chat_history": self.memory.messages
        })

        self.memory.add_user_message(user_input)
        self.memory.add_ai_message(answer)
        return {"agent": "WebOmniExpert", "answer": answer}