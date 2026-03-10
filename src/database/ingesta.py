import os
import sys
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.database.vector_engine import VectorEngine
from src.core.config import settings

def procesar_manuales():
    # 1. Obtener la conexión a ChromaDB
    vector_store = VectorEngine.get_vector_store()

    #2.Tamaño de los chunks y solapamiento para la división de texto
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    # Validar si la carpeta de manuales existe
    if not os.path.exists(settings.MANUALS_PATH):
        print(f"❌ Error: No existe la carpeta {settings.MANUALS_PATH}")
        return

    print(f"🔍 Buscando manuales en: {settings.MANUALS_PATH}...")
    archivos_encontrados = [f for f in os.listdir(settings.MANUALS_PATH) if f.endswith(".pdf")]

    if not archivos_encontrados:
        print("⚠️ No se encontraron archivos PDF para procesar.")
        return

    # 3. Procesar cada archivo
    for archivo in archivos_encontrados:
        path_completo = os.path.join(settings.MANUALS_PATH, archivo)
        print(f"📖 Procesando: {archivo}...")

        try:
            loader = PyPDFLoader(path_completo)
            # Cargamos y dividimos el PDF en trozos
            paginas = loader.load_and_split(text_splitter)

            # 4. Inyectar en la base de datos
            vector_store.add_documents(paginas)
            print(f"✅ {archivo} indexado correctamente ({len(paginas)} trozos).")
        except Exception as e:
            print(f"❌ Error procesando {archivo}: {e}")

if __name__ == "__main__":
    procesar_manuales()