# En Test/test_flow.py
import asyncio
from src.agents.graph import workflow
from src.core.memory import get_graph_checkpointer
from src.core.state import AgentState


async def test_complex_query():
    # 1. Obtener el gestor
    memory_manager = get_graph_checkpointer()

    # 2. Entrar en el contexto para obtener el saver real
    async with memory_manager as saver:
        # 3. Compilar el grafo dentro del contexto
        app_graph = workflow.compile(checkpointer=saver)

        # ... resto de la lógica de inputs y astream ...
        print("✅ Grafo compilado correctamente con AsyncSqliteSaver")