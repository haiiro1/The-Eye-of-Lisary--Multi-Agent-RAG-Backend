from typing import TypedDict, Annotated, Sequence, List
import operator
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    # 'operator.add' permite acumular mensajes de diferentes agentes en el historial
    messages: Annotated[Sequence[BaseMessage], operator.add]
    sheet_context: str
    language: str
    # Cola de agentes que el router decide invocar (ej: ["WEB", "BUILDER"])
    selected_agents: List[str]