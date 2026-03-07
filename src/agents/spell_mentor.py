from src.core.base_agent import BaseDnDAgent
from src.tools.rag_tool import RAGTool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from src.tools.wiki_tool import WikiTool

class SpellMentor(BaseDnDAgent):
    def _setup_tools(self):
        return {
            "wiki": WikiTool(),
            "rag": RAGTool(k=3),
        }

    def run(self, user_input: str, language: str = "es") -> dict:
        context = self.tools["rag"].search(user_input)

        prompt = ChatPromptTemplate.from_messages([
            ("system", "Eres el Mentor de Hechizos. Explica tiempos de lanzamiento, componentes y efectos en {lang}."),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "LIBRO DE HECHIZOS:\n{context}\n\nPREGUNTA: {question}")
        ])

        chain = prompt | self.llm | StrOutputParser()
        answer = chain.invoke({
            "context": context,
            "question": user_input,
            "lang": language,
            "chat_history": self.memory.messages
        })

        self.memory.add_user_message(user_input)
        self.memory.add_ai_message(answer)
        return {"agent": "SpellMentor", "answer": answer}