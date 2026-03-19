from typing import TypedDict, Annotated, Sequence, List
import operator
from langchain_core.messages import BaseMessage

# Definimos una función de reemplazo explícita
def replace_list(old_list: List[str], new_list: List[str]) -> List[str]:
    """Sobrescribe la lista anterior con la nueva versión (cola procesada)."""
    return new_list

class AgentState(TypedDict):
    # Los mensajes se acumulan (Correcto)
    messages: Annotated[Sequence[BaseMessage], operator.add]
    sheet_context: str
    language: str

    # IMPORTANTE: Usamos 'replace_list' para que cuando un nodo
    # haga el "pop", el estado realmente se actualice y no se duplique o mantenga el viejo.
    selected_agents: Annotated[List[str], replace_list]