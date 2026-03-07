from src.core.base_agent import BaseDnDAgent
from src.tools.sheet_manager import SheetManager
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

class SheetExpert(BaseDnDAgent):
    def _setup_tools(self):
        return SheetManager()

    def run(self, user_input: str, sheet_context: str, language: str = "es") -> dict:
        # Limpiamos el texto de la ficha antes de enviarlo al modelo
        clean_context = self.tools.format_sheet_context(sheet_context)

        prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres el Escriba del Ojo de Lisary.
             Extrae datos numéricos exactos de la ficha. No calcules manualmente.
             Si dice 'Rifle +12', responde +12. Si dice '2d10+7', responde eso.
             Responde siempre en {lang}. """),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "FICHA LIMPIA:\n{context}\n\nPREGUNTA: {question}")
        ])

        chain = prompt | self.llm | StrOutputParser()
        answer = chain.invoke({
            "context": clean_context,
            "question": user_input,
            "lang": language,
            "chat_history": self.memory.messages
        })

        self.memory.add_user_message(user_input)
        self.memory.add_ai_message(answer)
        return {"agent": "SheetExpert", "answer": answer}