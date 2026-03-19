import asyncio
import os
from src.core.config import DB_PATH
from src.database.persistence import get_graph_checkpointer
from src.agents.graph import agent_workflow
from src.core.logging_config import logger

async def verify_persistence():
    """
    Prueba que el checkpointer puede crear tablas y guardar un estado.
    """
    print(f"🔍 Verificando base de datos en: {DB_PATH}")

    try:
        async with get_graph_checkpointer() as saver:
            # 1. Compilar el grafo con el saver activo
            app = agent_workflow.compile(checkpointer=saver)

            # 2. Definir un thread de prueba
            config = {"configurable": {"thread_id": "test_connection_2026"}}

            # 3. Intentar una escritura mínima (Guardar un mensaje de sistema)
            initial_state = {"messages": [("system", "Prueba de inicialización de base de datos")]}

            # Usamos update_state para probar la escritura directa en la DB
            await app.aupdate_state(config, initial_state)

            # 4. Intentar leerlo de vuelta
            state = await app.aget_state(config)

            if state.values:
                print("✅ [SUCCESS]: Las tablas de LangGraph se han creado y la persistencia funciona.")
            else:
                print("⚠️ [WARNING]: El estado se guardó pero volvió vacío.")

    except Exception as e:
        print(f"❌ [ERROR]: Falló la inicialización de la base de datos: {e}")
        logger.error(f"Error detallado: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(verify_persistence())