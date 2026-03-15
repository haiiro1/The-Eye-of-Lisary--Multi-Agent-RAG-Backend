import os
import shutil
import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from src.database.vector_engine import VectorEngine
from src.core.config import settings
import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

def procesar_manuales():
    # 1. ELIMINACIÓN MANUAL (DEBES HACERLO ANTES DE CORRER EL SCRIPT)
    # Borra la carpeta data/vector_store manualmente para limpiar las 5000 letras.

    vector_store = VectorEngine.get_vector_store()

    # Configuramos el splitter con valores SEGUROS
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=250,
        separators=["\n\n", "\n", ". ", " "] # Jamás permitimos "" como separador aquí
    )

    archivos_pdf = [f for f in os.listdir(settings.MANUALS_PATH) if f.endswith('.pdf')]

    for archivo in archivos_pdf:
        path = os.path.join(settings.MANUALS_PATH, archivo)

        # --- EXTRACCIÓN ROBUSTA ---
        texto_unificado = ""
        with fitz.open(path) as doc:
            for pagina in doc:
                # Extraemos el texto y nos aseguramos de que sea un STRING plano
                texto_unificado += str(pagina.get_text("text")) + " "

        # LIMPIEZA DE CARACTERES NULOS
        texto_unificado = texto_unificado.replace('\x00', '').strip()

        print(f"📏 Caracteres totales en {archivo}: {len(texto_unificado)}")

        # --- CORTE SEGURO ---
        # Usamos split_text sobre el string gigante
        fragmentos_de_texto = text_splitter.split_text(texto_unificado)

        print(f"📦 Fragmentos generados: {len(fragmentos_de_texto)}")

        # Convertimos a documentos reales para Chroma
        docs_finales = [
            Document(page_content=txt, metadata={"source": archivo}) 
            for txt in fragmentos_de_texto if len(txt) > 50 # Ignoramos basura
        ]

        if docs_finales:
            vector_store.add_documents(docs_finales)
            print(f"✅ {archivo} indexado correctamente.")
if __name__ == "__main__":
    procesar_manuales()