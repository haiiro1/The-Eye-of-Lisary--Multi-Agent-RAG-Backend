import re
import json
from typing import List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.core.factory import LLMFactory
from src.core.logging_config import logger
from src.core.callbacks import get_langfuse_client

class DnDRouter:
    def __init__(self, callbacks=None):
        self.callbacks = callbacks
        self.llm = LLMFactory.get_model(is_reasoning=False, callbacks=self.callbacks)

    def classify_intent(self, user_input: str) -> List[str]:
        # 1. Validación de entrada
        if not user_input or not isinstance(user_input, str):
            return ["chat"]

        # Atajo manual para ahorrar tiempo y errores
        greetings = ["hola", "ola", "buenas", "saludos", "quien eres", "buenos dias"]
        if any(greet in user_input.lower() for greet in greetings):
            return ["chat"]

        try:
            # 2. Obtener prompt de Langfuse
            client = get_langfuse_client()
            prompt_res = client.get_prompt("dnd-router")
            
            # 3. Construir el prompt sin historial (el Router solo necesita la última pregunta)
            prompt = ChatPromptTemplate.from_messages([
                ("system", prompt_res.get_langchain_prompt()),
                ("human", "{input}")
            ])

            # 4. Cadena de ejecución
            chain = prompt | self.llm | StrOutputParser()
            
            # 5. Invocación pasando solo el string
            response = chain.invoke({"input": str(user_input)})
            
            # 6. Limpieza profunda del texto recibido
            text_response = re.sub(r'<think>.*?</think>', '', str(response), flags=re.DOTALL).strip()

            # 7. Extracción de JSON con "Fuerza Bruta"
            match = re.search(r'\[.*\]', text_response)
            if match:
                json_str = match.group().replace("'", '"')
                try:
                    intents = json.loads(json_str)
                    if isinstance(intents, list):
                        # Limpiar que sean strings válidos
                        return [str(i).strip().lower() for i in intents if i]
                except:
                    logger.warning(f"⚠️ Error parseando JSON en Router: {json_str}")
            
            return ["chat"]

        except Exception as e:
            # Si esto falla, el log nos dirá la verdad
            logger.error(f"❌ Error real en Router: {e}")
            return ["chat"]