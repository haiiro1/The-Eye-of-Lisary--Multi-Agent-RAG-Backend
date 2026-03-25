import asyncio
from src.agents.graph import agent_workflow
from src.database.persistence import get_graph_checkpointer
from langchain_core.messages import HumanMessage

async def test_full_flow():
    # 1. Configurar persistencia para la prueba
    checkpointer_cm = get_graph_checkpointer()
    async with checkpointer_cm as saver:
        app_graph = agent_workflow.compile(checkpointer=saver)
        # 2. Definir estado inicial
        initial_state = {
            'messages': [HumanMessage(content='¿Qué beneficios obtengo al lanzar una Bola de Fuego siendo un mago de la Escuela de Evocación?')],
            'language': 'es',
            'selected_agents': []
        }
        config = {'configurable': {'thread_id': 'test_session_1'}}

        # 3. Ejecutar el grafo
        print('\n--- 👁️ El Ojo de Lisary está procesando tu visión... ---\n')
        final_state = await app_graph.ainvoke(initial_state, config)
        # 4. Mostrar respuesta final del Agregador
        print(f'RESPUESTA FINAL:\n{final_state["messages"][-1].content}')

asyncio.run(test_full_flow())