from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from contextlib import asynccontextmanager
import uvicorn
import PyPDF2
import io
import os

from src.core.logging_config import logger
from src.core.memory import get_graph_checkpointer
from src.agents.graph import workflow

# --- CONFIGURACIÓN DE DIRECTORIOS ---
os.makedirs("data/manuales", exist_ok=True)
os.makedirs("data/vector_store", exist_ok=True)

# Variables globales para el motor
app_graph = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestiona el ciclo de vida del checkpointer y el grafo."""
    global app_graph
    checkpointer = get_graph_checkpointer()

    # Conectamos el saver asíncrono (aiosqlite)
    async with checkpointer as saver:
        # Compilamos el grafo con la conexión activa
        app_graph = workflow.compile(checkpointer=saver)
        logger.info("✅ El Ojo de Lisary ha despertado con Lifespan y AsyncCheckpointer.")
        yield
        # La conexión se cierra automáticamente al salir del bloque 'async with'

app = FastAPI(
    title="The Eye of Lisary API",
    version="2.0.0",
    description="Backend multi-agente RAG para D&D 5e orquestado con LangGraph.",
    lifespan=lifespan
)

# Almacenamiento temporal en memoria para las fichas (en producción usar DB/Redis)
fichas_personajes = {}

class ChatRequest(BaseModel):
    message: str
    session_id: str

# --- ENDPOINTS ---

@app.get("/")
async def root():
    return {
        "status": "Online",
        "system": "The Eye of Lisary",
        "engine": "LangGraph + Asynchronous Persistence"
    }

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
        # Recuperamos el contexto de la ficha si existe
        contexto_ficha = fichas_personajes.get(request.session_id, "No hay ficha cargada.")

        initial_state = {
            "messages": [("human", request.message)],
            "sheet_context": contexto_ficha,
            "language": "es",
            "selected_agents": []  # Lista para la orquestación secuencial
        }

        config = {"configurable": {"thread_id": request.session_id}}

        # Invocación asíncrona (obligatoria para AsyncSqliteSaver)
        final_state = await app_graph.ainvoke(initial_state, config)

        # Extraemos el contenido del último mensaje (respuesta del Agregador)
        last_message = final_state["messages"][-1]
        response_content = last_message.content if hasattr(last_message, 'content') else str(last_message)

        return {
            "response": response_content,
            "session_id": request.session_id,
            "agents_involved": final_state.get("selected_agents", []) # Para debug
        }
    except Exception as e:
        logger.error(f"❌ Error en el flujo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload_sheet/{session_id}")
async def upload_sheet(session_id: str, file: UploadFile = File(...)):
    """Procesa un PDF de ficha de personaje y lo vincula a la sesión."""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Solo se admiten archivos PDF.")

    try:
        content = await file.read()
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        text_content = ""

        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_content += page_text + "\n"

        if not text_content.strip():
            raise ValueError("El PDF no contiene texto extraíble.")

        fichas_personajes[session_id] = text_content
        logger.info(f"📄 Ficha vinculada a sesión: {session_id}")

        return {"status": "success", "message": "Ficha vinculada correctamente."}
    except Exception as e:
        logger.error(f"❌ Error procesando PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)