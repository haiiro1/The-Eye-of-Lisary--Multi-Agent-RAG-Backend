# importaciones estándar
import os
from chromadb.app import settings
import uvicorn
import fitz  # PyMuPDF
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from contextlib import asynccontextmanager
# importaciones internas
from langfuse.langchain import CallbackHandler
from src.core.logging_config import logger
from src.database.persistence import get_graph_checkpointer
from src.agents.graph import agent_workflow
from src.core.callbacks import get_langfuse_callback

# --- CONFIGURACIÓN DE DIRECTORIOS ---
os.makedirs("data/manuales", exist_ok=True)
os.makedirs("data/vector_store", exist_ok=True)

# Variable global para el grafo compilado
app_graph = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestiona el ciclo de vida de la aplicación y la conexión persistente a la DB.
    """
    global app_graph

    # Obtenemos el context manager del checkpointer
    checkpointer_cm = get_graph_checkpointer()

    # Entramos en el contexto asíncrono y lo mantenemos vivo
    async with checkpointer_cm as saver:
        # Compilamos el grafo vinculando el saver activo
        app_graph = agent_workflow.compile(checkpointer=saver)
        logger.info("✅ El Ojo de Lisary ha despertado con AsyncCheckpointer (SQLite).")

        yield  # Aquí es donde la API se mantiene "corriendo"

    logger.info("💤 El Ojo de Lisary se ha dormido y la conexión DB se ha cerrado.")

app = FastAPI(
    title="The Eye of Lisary API",
    version="2.1.0",
    description="Backend multi-agente RAG optimizado con PyMuPDF y LangGraph v0.2+",
    lifespan=lifespan
)

# Diccionario temporal para fichas (Considera persistirlo en DB si es necesario)
fichas_personajes = {}

class ChatRequest(BaseModel):
    message: str
    session_id: str

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
        # Handler de monitoreo
        handler = get_langfuse_callback(session_id=request.session_id)
        # Estado inicial para el grafo
        initial_state = {
            "messages": [("human", request.message)],
            "sheet_context": fichas_personajes.get(request.session_id, ""),
            "language": "es",
            "selected_agents": []
        }

        # Configuración de la sesión (Thread Persistence)
        config = {
            "configurable": {"thread_id": request.session_id},
            "callbacks": [handler],
            "metadata": {"interface": "streamlit_ui", "version": "2.0"}
        }

        # Ejecución asíncrona (ainvoke usará automáticamente el checkpointer del compile)
        final_state = await app_graph.ainvoke(initial_state, config)

        # Extraer respuesta
        last_message = final_state["messages"][-1]

        # El contenido puede ser string o base_message de LangChain
        response_content = last_message.content if hasattr(last_message, 'content') else str(last_message)

        return {
            "response": response_content,
            "session_id": request.session_id,
            "agents_involved": final_state.get("selected_agents", [])
        }
    except Exception as e:
        logger.error(f"❌ Error en el flujo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.post("/upload_sheet/{session_id}")
async def upload_sheet(session_id: str, file: UploadFile = File(...)):
    """Procesa una ficha de personaje usando fitz."""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Solo se admiten archivos PDF.")

    try:
        content = await file.read()
        with fitz.open(stream=content, filetype="pdf") as doc:
            text_content = ""
            for pagina in doc:
                text_content += pagina.get_text("text").replace('\x00', '') + "\n"

        if not text_content.strip():
            raise ValueError("El PDF no contiene texto extraíble.")

        fichas_personajes[session_id] = text_content
        logger.info(f"📄 Ficha procesada con fitz para sesión: {session_id}")

        return {"status": "success", "message": "Ficha vinculada correctamente."}
    except Exception as e:
        logger.error(f"❌ Error procesando PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)