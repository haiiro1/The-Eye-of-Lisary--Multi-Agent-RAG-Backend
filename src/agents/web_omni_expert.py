from src.core.base_agent import BaseDnDAgent
from src.tools.wiki_tool import WikiTool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

class WebOmniExpert(BaseDnDAgent):
    def _setup_tools(self):
        return WikiTool()

    def run(self, user_input: str, language: str = "es") -> dict:
        # Buscamos en todo el ecosistema web de D&D
        web_results = self.tools.search_all_dnd(user_input)

        prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres el Gran Cronista de la Red del Ojo de Lisary.
             Tu misión es filtrar la información de la web (Wikidot y Dandwiki).

             PROTOCOLOS DE RESPUESTA:
             1. IDIOMA: Responde en {lang}.
             2. DISTINCIÓN DE FUENTES:
                - Si la info viene de WIKIDOT, márcala como 'CONTENIDO OFICIAL (Expansiones)'.
                - Si la info viene de DANDWIKI, márcala como 'CONTENIDO HOMEBREW (No Oficial)'.
             3. TRADUCCIÓN: Mantén términos técnicos en inglés entre paréntesis: 'Puntos de Golpe (Hit Points)'.
             4. ADVERTENCIA: Si usas Homebrew, advierte sobre el balanceo del juego.
             5. SÍNTESIS: Si encuentras la misma dote o clase en ambos sitios, explica las diferencias."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "RESULTADOS DE BÚSQUEDA WEB:\n{context}\n\nPREGUNTA DEL JUGADOR: {question}")
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