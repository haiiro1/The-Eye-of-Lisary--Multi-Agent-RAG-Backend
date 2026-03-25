from typing import Dict, Any, Optional
from src.core.base_agent import BaseDnDAgent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableConfig
from src.core.callbacks import get_langfuse_client
from src.core.logging_config import logger

class WebOmniExpert(BaseDnDAgent):
    def _setup_tools(self):
        # La información externa (Tavily/Wikipedia) llega vía extra_info
        return {}

    def run(self, user_input: str, language: str = "es", extra_info: str = "", config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
        logger.info(f"🌐 [WebOmniExpert] Consultando las crónicas del mundo...")

        client = get_langfuse_client()
        prompt_res = client.get_prompt("dnd-web-expert")

        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_res.get_langchain_prompt()),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", """INFORMACIÓN RECOPILADA DEL MUNDO (WEB/LORE):
            {extra_info}

            CONSULTA DEL MORTAL:
            {question}""")
        ])

        chain = prompt | self.llm | StrOutputParser()

        answer = chain.invoke({
            "extra_info": extra_info,
            "question": user_input,
            "lang": language,
            "chat_history": self.memory_messages
        }, config=config)

        return {"agent": "WebOmniExpert", "answer": answer}