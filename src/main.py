from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from contextlib import asynccontextmanager
from src.core.logging_config import logger
from src.core.memory import get_graph_checkpointer
from src.agents.graph import workflow
import uvicorn
import fitz  # PyMuPDF
import os
from src.core.config import settings
from langfuse import CallbackHandler, LangfuseHandler



# --- CONFIGURACIÓN DE DIRECTORIOS ---
os.makedirs("data/manuales", exist_ok=True)
os.makedirs("data/vector_store", exist_ok=True)

app_graph = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global app_graph
    checkpointer = get_graph_checkpointer()
    async with checkpointer as saver:
        app_graph = workflow.compile(checkpointer=saver)
        logger.info("✅ El Ojo de Lisary ha despertado con fitz y AsyncCheckpointer.")
        yield

app = FastAPI(
    title="The Eye of Lisary API",
    version="2.1.0",
    description="Backend multi-agente RAG optimizado con PyMuPDF.",
    lifespan=lifespan
)

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
    # ... validaciones de app_graph ...
    if not app_graph:
        raise HTTPException(status_code=503, detail="Motor no inicializado.")
    try:
        # Instancia actualizada del handler para Langfuse v2
        langfuse_handler = CallbackHandler(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_HOST,
            session_id=request.session_id,
            # 'metadata' permite añadir datos extra útiles para D&D
            metadata={"interface": "fastapi", "engine": "fitz"}
        )

        initial_state = {
            "messages": [("human", request.message)],
            "sheet_context": fichas_personajes.get(request.session_id, ""),
            "language": "es",
            "selected_agents": []
        }

        # Configuración del grafo incluyendo el callback
        config = {
            "configurable": {"thread_id": request.session_id},
            "callbacks": [langfuse_handler]
        }

        # Ejecución asíncrona
        final_state = await app_graph.ainvoke(initial_state, config)

        last_message = final_state["messages"][-1]
        return {
            "response": last_message.content if hasattr(last_message, 'content') else str(last_message),
            "session_id": request.session_id,
            "agents_involved": final_state.get("selected_agents", [])
        }
    except Exception as e:
        logger.error(f"❌ Error en el flujo: {e}")
        raise HTTPException(status_code=500, detail=f"Error en el motor: {str(e)}")

@app.post("/upload_sheet/{session_id}")
async def upload_sheet(session_id: str, file: UploadFile = File(...)):
    """Procesa una ficha de personaje usando fitz (más eficiente)."""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Solo se admiten archivos PDF.")

    try:
        content = await file.read()
        # Abrimos el PDF desde la memoria con fitz
        with fitz.open(stream=content, filetype="pdf") as doc:
            text_content = ""
            for pagina in doc:
                # Extraemos texto eliminando caracteres nulos, igual que en ingesta.py
                text_content += pagina.get_text("text").replace('\x00', '') + "\n"

        if not text_content.strip():
            raise ValueError("El PDF no contiene texto extraíble o está vacío.")

        # Guardamos el texto para que el builder_node lo recupere del estado
        fichas_personajes[session_id] = text_content
        logger.info(f"📄 Ficha procesada con fitz para sesión: {session_id}")

        return {"status": "success", "message": "Ficha vinculada correctamente con fitz."}
    except Exception as e:
        logger.error(f"❌ Error procesando PDF con fitz: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)