from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from src.agents.router import DnDRouter
import uvicorn
import PyPDF2
import io
from src.core.logging_config import logger

app = FastAPI(title="The Eye of Lisary API", version="1.1.0")

# Instanciamos el Router globalmente
router_principal = DnDRouter()

# Diccionario temporal para guardar el texto de las fichas por sesión
# En producción, esto iría a una base de datos o caché (Redis)
fichas_personajes = {}

class ChatRequest(BaseModel):
    message: str
    session_id: str

@app.get("/")
async def root():
    return {"status": "Ojo de Lisary Online", "message": "Listo para la aventura y la lectura de fichas."}

@app.post("/upload_sheet/{session_id}")
async def upload_sheet(session_id: str, file: UploadFile = File(...)):
    """Carga y procesa la ficha PDF del personaje (ej: Wade Grayrat)"""
    try:
        content = await file.read()
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        text_content = ""
        for page in pdf_reader.pages:
            text_content += page.extract_text()

        # Guardamos el texto extraído para esta sesión
        fichas_personajes[session_id] = text_content

        logger.info(f"📄 Ficha cargada para sesión {session_id}. Personaje detectado.")
        return {
            "status": "success",
            "message": f"Ficha de {session_id} procesada exitosamente.",
            "preview": text_content[:150] + "..."
        }
    except Exception as e:
        logger.error(f"❌ Error al procesar PDF: {e}")
        raise HTTPException(status_code=500, detail="No se pudo leer el PDF de la ficha.")

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        # Recuperamos el contexto de la ficha si existe para este usuario
        contexto_ficha = fichas_personajes.get(request.session_id, "No hay ficha cargada.")

        # El Router ahora recibe el input, la sesión y el contexto de la ficha
        # Nota: Debes actualizar la firma de router.route() si quieres pasar el contexto directo
        data = router_principal.route(
            user_input=request.message,
            session_id=request.session_id,
            sheet_context=contexto_ficha # <--- Nuevo parámetro
        )

        return {
            "agent_used": data["agent"],
            "response": data["answer"],
            "session_id": request.session_id
        }
    except Exception as e:
        logger.error(f"❌ Error en el endpoint /chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)