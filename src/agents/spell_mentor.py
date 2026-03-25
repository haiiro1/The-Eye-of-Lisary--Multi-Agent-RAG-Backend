from typing import Dict, Any
from src.core.base_agent import BaseDnDAgent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableConfig
from src.core.callbacks import get_langfuse_client

class SpellMentor(BaseDnDAgent):
    def _setup_tools(self):
        return {}

    def run(self, user_input: str, language: str = "es", extra_info: str = "", config: RunnableConfig = None) -> Dict[str, Any]:
        client = get_langfuse_client()
        prompt_res = client.get_prompt("dnd-spell-expert")
        prompt_tpl = ChatPromptTemplate.from_template(prompt_res.get_langchain_prompt())

        chain = prompt_tpl | self.llm | StrOutputParser()

        answer = chain.invoke({
            "user_input": user_input,
            "extra_info": extra_info,
            "language": language
        }, config=config)

        return {"answer": answer}