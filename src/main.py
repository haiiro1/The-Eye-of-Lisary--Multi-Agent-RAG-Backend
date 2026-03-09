from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from src.agents.router import DnDRouter
import uvicorn
import PyPDF2
import io
from src.core.logging_config import logger

app = FastAPI(
    title="The Eye of Lisary API",
    version="1.2.0",
    description="Backend multiagente RAG para D&D 5e con soporte para fichas PDF."
)

# Instanciamos el Router globalmente para mantener los agentes calientes en memoria
router_principal = DnDRouter()

# Almacén de fichas (En una fase posterior, esto debería ser Redis o una DB)
fichas_personajes = {}

class ChatRequest(BaseModel):
    message: str
    session_id: str

@app.get("/")
async def root():
    return {
        "status": "Online",
        "artifact": "Ojo de Lisary",
        "message": "Listo para procesar manuales, hechizos y fichas de héroes."
    }

@app.post("/upload_sheet/{session_id}")
async def upload_sheet(session_id: str, file: UploadFile = File(...)):
    """
    Carga y procesa la ficha PDF del personaje.
    Extrae el texto para que el SheetExpert pueda analizarlo.
    """
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
            raise ValueError("El PDF parece estar vacío o ser una imagen (no contiene texto seleccionable).")

        # Guardamos el texto extraído asociado a la sesión
        fichas_personajes[session_id] = text_content

        logger.info(f"📄 Ficha procesada para la sesión: {session_id}.")
        return {
            "status": "success",
            "session_id": session_id,
            "message": "Ficha vinculada correctamente.",
            "characters_stats_detected": len(text_content)
        }
    except Exception as e:
        logger.error(f"❌ Error al procesar PDF en sesión {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Endpoint principal de conversación.
    Recupera el contexto de la ficha y delega la lógica al Router.
    """
    try:
        # Recuperamos el contexto de la ficha o indicamos su ausencia
        contexto_ficha = fichas_personajes.get(request.session_id, "No hay ficha cargada.")

        # El Router se encarga de la orquestación multia-agente
        data = router_principal.route(
            user_input=request.message,
            session_id=request.session_id,
            sheet_context=contexto_ficha
        )

        return {
            "agent_used": data["agent"],
            "response": data["answer"],
            "session_id": request.session_id
        }
    except Exception as e:
        logger.error(f"❌ Error en el flujo de chat: {e}")
        raise HTTPException(status_code=500, detail="El Ojo ha tenido un problema interno. Revisa los logs.")

if __name__ == "__main__":
    # Configuración de inicio para desarrollo
    uvicorn.run(app, host="0.0.0.0", port=8000)