import uvicorn
import fitz
import json
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
import asyncio
import logging


# Importaciones internas
from src.core.logging_config import logger
from src.database.persistence import get_graph_checkpointer
from src.agents.graph import agent_workflow
from src.core.callbacks import get_langfuse_callback

logging.getLogger("opentelemetry.context").setLevel(logging.CRITICAL)
logging.getLogger("opentelemetry.exporter.otlp.proto.http.trace_exporter").setLevel(logging.CRITICAL)

app_graph = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global app_graph
    checkpointer_cm = get_graph_checkpointer()
    async with checkpointer_cm as saver:
        app_graph = agent_workflow.compile(checkpointer=saver)
        logger.info("✅ El Ojo de Lisary ha despertado.")
        yield
    logger.info("💤 El Ojo de Lisary se ha dormido.")

app = FastAPI(
    title="The Eye of Lisary API",
    version="2.1.2",
    description="Backend optimizado con supresión de ruidos de telemetría",
    lifespan=lifespan
)

fichas_personajes = {}

class ChatRequest(BaseModel):
    message: str
    session_id: str

async def response_generator(request: ChatRequest):
    """Generador con gestión de cierre de trazas para Langfuse."""
    handler = get_langfuse_callback(session_id=request.session_id)

    initial_state = {
        "messages": [("human", request.message)],
        "sheet_context": fichas_personajes.get(request.session_id, ""),
        "language": "es",
        "selected_agents": []
    }

    config = {
        "configurable": {"thread_id": request.session_id},
        "callbacks": [handler],
        "metadata": {"interface": "api", "version": "2.1.2"}
    }

    try:
        async for event in app_graph.astream_events(initial_state, config, version="v2"):
            kind = event["event"]
            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    yield f"data: {json.dumps({'token': content})}\n\n"
    except Exception as e:
        logger.error(f"❌ Error en el generador: {e}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
    finally:
        # Importante: Damos un breve respiro para que el callback envíe los datos a Langfuse
        # antes de que FastAPI destruya el contexto de la petición.
        await asyncio.sleep(0.2)
        yield "data: [DONE]\n\n"

# --- ENDPOINTS ---

@app.get("/")
async def root():
    return {"status": "Online", "system": "The Eye of Lisary"}

@app.get("/health")
async def health_check():
    return {
        "status": "Healthy",
        "graph_initialized": app_graph is not None
    }

@app.post("/chat")
async def chat(request: ChatRequest):
    """Endpoint de chat con soporte de Streaming."""
    if not app_graph:
        raise HTTPException(status_code=503, detail="Motor no inicializado.")

    return StreamingResponse(response_generator(request), media_type="text/event-stream")

@app.post("/upload_sheet/{session_id}")
async def upload_sheet(session_id: str, file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Solo se admiten archivos PDF.")

    try:
        content = await file.read()
        with fitz.open(stream=content, filetype="pdf") as doc:
            text_content = "".join([p.get_text("text").replace('\x00', '') + "\n" for p in doc])

        if not text_content.strip():
            raise ValueError("El PDF no contiene texto extraíble.")

        fichas_personajes[session_id] = text_content
        return {"status": "success", "message": "Ficha vinculada correctamente."}
    except Exception as e:
        logger.error(f"❌ Error procesando PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)