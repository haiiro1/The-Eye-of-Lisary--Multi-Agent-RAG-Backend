import uvicorn
import json
import os
import tempfile
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from contextlib import asynccontextmanager


import logging

from src.core.logging_config import logger
from src.database.persistence import get_graph_checkpointer
from src.agents.graph import agent_workflow
from src.core.callbacks import get_langfuse_callback
from src.tools.sheet_manager import SheetManager
from langchain_core.messages import HumanMessage, AIMessage

# --- CONFIGURACIÓN DE DIRECTORIOS ---
os.makedirs("data/manuales", exist_ok=True)
os.makedirs("data/vector_store", exist_ok=True)
"""
silenciar error de opentelemetry ocurre porque Langfuse y FastAPI están intentando cerrar el contexto
de rastreo en hilos diferentes debido al uso de ainvoke en un entorno asíncrono.
"""


logging.getLogger("opentelemetry.context").setLevel(logging.CRITICAL)
# Variable global para el grafo compilado
app_graph = None
fichas_personajes = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    global app_graph
    checkpointer_cm = get_graph_checkpointer()
    # Mantenemos el contexto abierto durante TODA la ejecución
    async with checkpointer_cm as saver:
        app_graph = agent_workflow.compile(checkpointer=saver)
        logger.info("✅ El Ojo de Lisary ha despertado.")
        yield 
    logger.info("💤 El Ojo de Lisary se ha dormido.")


app = FastAPI(
    title="The Eye of Lisary API",
    version="2.2.0",
    description="Backend sheet_manager integrado",
    lifespan=lifespan
)

class ChatRequest(BaseModel):
    message: str
    session_id: str

async def response_generator(request: ChatRequest):
    """
    permite que el usuario vea cómo se escribe la respuesta palabra por palabra,
    en lugar de esperar 5 o 10 segundos a que el modelo termine de procesar todo.
    """
    handler = get_langfuse_callback(session_id=request.session_id)
    initial_state = {
        "messages": [("human", request.message)],
        "sheet_context": fichas_personajes.get(request.session_id, ""),
        "language": "es"
    }
    config = {"configurable": {"thread_id": request.session_id}, "callbacks": [handler]}

    try:
        async for event in app_graph.astream_events(initial_state, config, version="v2"):
            if event["event"] == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    yield f"data: {json.dumps({'token': content})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
    finally:
        yield "data: [DONE]\n\n"

# --- ENDPOINTS ---

@app.get("/")
async def root():
    return {"status": "Online", "system": "The Eye of Lisary", "pdf_engine": "PyMuPDF (fitz)"}

@app.get("/health")
async def health_check():
    return {
        "status": "Healthy",
        "graph_initialized": app_graph is not None
    }

@app.post("/chat")
async def chat(request: ChatRequest):
    if not app_graph:
        raise HTTPException(status_code=503, detail="Motor no inicializado.")

    try:
        handler = get_langfuse_callback(session_id=request.session_id)
        initial_state = {
            "messages": [HumanMessage(content=request.message)], # <--- CAMBIA LA TUPLA POR ESTO
            "sheet_context": fichas_personajes.get(request.session_id, ""),
            "language": "es",
            "selected_agents": []
        }
        config = {
            "configurable": {"thread_id": request.session_id},
            "callbacks": [handler]
        }

        final_state = await app_graph.ainvoke(initial_state, config)
        last_message = final_state["messages"][-1]

        response_content = last_message.content if hasattr(last_message, 'content') else str(last_message)

        return {
            "response": response_content,
            "session_id": request.session_id,
            "agents_involved": final_state.get("selected_agents", [])
        }
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload_sheet/{session_id}")
async def upload_sheet(session_id: str, file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Solo PDF.")

    content = await file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # 1. Procesar widgets
        raw_data = SheetManager.process_pdf(tmp_path)
        # 2. Formatear para el contexto del Agente
        formatted = SheetManager.format_sheet_context(raw_data)
        fichas_personajes[session_id] = formatted

        logger.info(f"✅ Ficha vinculada a {session_id}")
        return {"status": "success", "nombre": raw_data.get("nombre", "Atlas")}
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)