from src.core.base_agent import BaseDnDAgent
from src.tools.wiki_tool import WikiTool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from src.core.logging_config import logger

class WebOmniExpert(BaseDnDAgent):
    def _setup_tools(self):
        # El experto web usa su herramienta dedicada para buscar en wikis específicas
        return WikiTool()

    def run(self, user_input: str, language: str = "es") -> dict:
        logger.info(f"🌐 [WebOmniExpert] Consultando fuentes externas (Wikidot/Dandwiki)...")

        # 1. Ejecución de la búsqueda web
        web_results = self.tools.search_all_dnd(user_input)

        # 2. Prompt Maestro del Cronista (Evolucionado)
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres el Cronista Omnisciente de la Red, un archimago que filtra la sabiduría de los planos digitales.
             Tu misión es organizar la información externa de D&D 5e de forma profesional y estructurada.

             REGLAS DE FORMATO Y CONTENIDO:
             1. CLASIFICACIÓN: Identifica claramente si la fuente es 'WIKIDOT' (Oficial/SRD) o 'DANDWIKI' (Homebrew/Fan-made).
             
             2. ESTRUCTURA DE HECHIZOS: Si la información es un conjuro, preséntalo así:
                ### [Nombre del Hechizo]
                *Nivel y Escuela*
                - **Tiempo de lanzamiento:** - **Alcance:** - **Componentes:** - **Duración:** > [Descripción del efecto]

             3. ESTRUCTURA DE REGLAS: Usa negritas para términos mecánicos y listas claras para condiciones o pasos.

             4. ADVERTENCIA HOMEBREW: Si los datos provienen de 'Dandwiki', DEBES iniciar la respuesta con: 
                "⚠️ **Nota del Cronista:** Esta información es Homebrew (contenido de fans) y puede no estar balanceada para partidas oficiales."

             5. COMPARACIÓN: Si encuentras la misma regla en ambas fuentes, prioriza Wikidot y menciona que la versión de Dandwiki es una variante.

             IDIOMA: Responde siempre en {lang}.
             TONO: Épico, sabio y extremadamente organizado."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "RESULTADOS DE BÚSQUEDA WEB:\n{context}\n\nPREGUNTA DEL JUGADOR: {question}")
        ])

        chain = prompt | self.llm | StrOutputParser()

        # Invocamos la cadena
        answer = chain.invoke({
            "context": web_results,
            "question": user_input,
            "lang": language,
            "chat_history": self.memory.messages # Esto lee el historial
        })

        # --- ELIMINAMOS LA LÍNEA: self.memory.save_message(...) ---
        # No es necesaria porque el nodo de LangGraph se encarga de la memoria
        # al retornar el mensaje al final de la ejecución.

        return {"agent": "WebOmniExpert", "answer": answer}