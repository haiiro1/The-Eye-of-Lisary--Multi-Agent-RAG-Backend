from typing import TypedDict, Annotated, Sequence
import operator
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    # 'operator.add' permite que los nuevos mensajes se añadan al historial en lugar de sobrescribirlo
    messages: Annotated[Sequence[BaseMessage], operator.add]
    sheet_context: str
    language: str
    next_step: str  # Controla el flujo del grafo