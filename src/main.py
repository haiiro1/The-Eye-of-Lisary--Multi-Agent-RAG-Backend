from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
import uvicorn
import PyPDF2
import io
import os
from src.core.logging_config import logger
# Importamos el grafo desde su ubicación original
from src.agents.graph import app_graph

# Aseguramos que existan las carpetas de datos al iniciar
os.makedirs("data/manuales", exist_ok=True)
os.makedirs("data/vector_store", exist_ok=True)

# EXPOSICIÓN PARA GUI_TEST: Creamos un alias llamado 'graph'
# para que coincida con lo que busca tu script de Streamlit
graph = app_graph

app = FastAPI(
    title="The Eye of Lisary API - LangGraph Edition",
    version="2.0.0",
    description="Backend multi-agente RAG para D&D 5e orquestado con LangGraph."
)

fichas_personajes = {}

class ChatRequest(BaseModel):
    message: str
    session_id: str

@app.get("/")
async def root():
    return {
        "status": "Online",
        "system": "The Eye of Lisary",
        "engine": "LangGraph + Fireworks AI"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "Healthy",
        "message": "The Eye of Lisary API is running smoothly."
    }

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        contexto_ficha = fichas_personajes.get(request.session_id, "No hay ficha cargada.")

        # Estado inicial alineado con tu AgentState
        initial_state = {
            "messages": [("human", request.message)],
            "sheet_context": contexto_ficha,
            "language": "es",
            "next_step": ""
        }

        config = {"configurable": {"thread_id": request.session_id}}

        # Invocamos el grafo usando el objeto importado
        final_state = app_graph.invoke(initial_state, config)

        # Obtenemos el contenido del último mensaje (la respuesta del agente)
        last_message = final_state["messages"][-1]

        return {
            "agent_used": final_state.get("next_step", "Finalizer"),
            "response": last_message.content if hasattr(last_message, 'content') else str(last_message),
            "session_id": request.session_id
        }

    except Exception as e:
        logger.error(f"❌ Error en el flujo de LangGraph: {e}")
        raise HTTPException(status_code=500, detail="Error interno en el orquestador.")

@app.post("/upload_sheet/{session_id}")
async def upload_sheet(session_id: str, file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
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