from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from contextlib import asynccontextmanager
from src.core.logging_config import logger
from src.core.memory import get_graph_checkpointer
from src.agents.graph import workflow
import uvicorn
import PyPDF2
import io
import os



# --- CONFIGURACIÓN DE DIRECTORIOS ---
os.makedirs("data/manuales", exist_ok=True)
os.makedirs("data/vector_store", exist_ok=True)

app_graph = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestiona el ciclo de vida del checkpointer y el grafo."""
    global app_graph
    try:
        checkpointer = get_graph_checkpointer()
        # Conectamos el saver asíncrono
        async with checkpointer as saver:
            # Compilamos el grafo con persistencia
            app_graph = workflow.compile(checkpointer=saver)
            logger.info("✅ El Ojo de Lisary ha despertado con Lifespan y AsyncCheckpointer.")
            yield
    except Exception as e:
        logger.error(f"❌ Error al iniciar el grafo: {e}")
        yield

app = FastAPI(
    title="The Eye of Lisary API",
    version="2.0.0",
    description="Backend multi-agente RAG para D&D 5e orquestado con LangGraph.",
    lifespan=lifespan
)

fichas_personajes = {}

class ChatRequest(BaseModel):
    message: str
    session_id: str

# --- ENDPOINTS ---

@app.post("/chat")
async def chat(request: ChatRequest):
    if not app_graph:
        raise HTTPException(status_code=503, detail="Motor no inicializado.")

    try:
        # Recuperamos la ficha vinculada a la sesión
        contexto_ficha = fichas_personajes.get(request.session_id, "No hay ficha cargada.")

        # Preparamos el estado inicial
        initial_state = {
            "messages": [("human", request.message)],
            "sheet_context": contexto_ficha,
            "language": "es",
            "selected_agents": []
        }

        # Configuración de hilo para la persistencia
        config = {"configurable": {"thread_id": request.session_id}}

        # Invocación asíncrona
        final_state = await app_graph.ainvoke(initial_state, config)

        # Robustez en la extracción de la respuesta final (Aggregator)
        last_message = final_state["messages"][-1]
        if hasattr(last_message, 'content'):
            response_content = last_message.content
        elif isinstance(last_message, tuple):
            response_content = last_message[1]
        else:
            response_content = str(last_message)

        return {
            "response": response_content,
            "session_id": request.session_id,
            # Nota: selected_agents estará vacío aquí porque el Aggregator lo limpia al terminar
        }
    except Exception as e:
        logger.error(f"❌ Error en el flujo: {e}")
        raise HTTPException(status_code=500, detail=f"Error en el motor: {str(e)}")

@app.post("/upload_sheet/{session_id}")
async def upload_sheet(session_id: str, file: UploadFile = File(...)):
    """Extrae texto de PDF y lo guarda en memoria para el CharBuilder."""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Solo se admiten archivos PDF.")

    try:
        content = await file.read()
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        text_content = ""

        for page in pdf_reader.pages:
            text_content += page.extract_text() or ""

        if not text_content.strip():
            raise ValueError("El PDF está vacío o no es legible.")

        # Guardamos el texto para que el builder_node lo recupere del estado
        fichas_personajes[session_id] = text_content
        logger.info(f"📄 Ficha procesada para sesión: {session_id}")

        return {"status": "success", "message": "Ficha vinculada correctamente."}
    except Exception as e:
        logger.error(f"❌ Error procesando PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)