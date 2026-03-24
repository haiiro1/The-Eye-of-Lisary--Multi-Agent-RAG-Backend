import os
import fitz  # PyMuPDF
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from src.database.vector_engine import VectorEngine
from src.core.config import settings
from src.core.logging_config import logger

def procesar_manuales_por_pagina():
    """
    Lee los PDFs de la carpeta de manuales, los fragmenta y los indexa en ChromaDB.
    """
    # 1. Asegurar que la ruta de manuales existe
    if not os.path.exists(settings.MANUALS_PATH):
        os.makedirs(settings.MANUALS_PATH, exist_ok=True)
        logger.warning(f"⚠️ Carpeta de manuales creada en {settings.MANUALS_PATH}. Añade PDFs allí.")
        return

    # 2. Inicializar el motor vectorial y el splitter
    vector_store = VectorEngine.get_vector_store()
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150, 
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    # Palabras clave para omitir contenido no técnico
    SKIP_KEYWORDS = ["CRÉDITOS", "AGRADECIMIENTOS", "BIBLIOGRAFÍA", "LITERATURA INSPIRADORA", "ÍNDICE"]

    archivos_pdf = [f for f in os.listdir(settings.MANUALS_PATH) if f.endswith('.pdf')]

    if not archivos_pdf:
        logger.info("📭 No se encontraron archivos PDF para procesar en la ruta configurada.")
        return

    for archivo in archivos_pdf:
        path = os.path.join(settings.MANUALS_PATH, archivo)
        logger.info(f"📄 Iniciando procesamiento: {archivo}")

        try:
            with fitz.open(path) as doc:
                todas_las_paginas_docs = []

                for i, pagina in enumerate(doc):
                    # Extracción y limpieza de caracteres nulos
                    texto_raw = pagina.get_text("text")
                    texto_pagina = texto_raw.replace('\x00', '').strip()

                    # Filtro 1: Páginas con contenido insuficiente
                    if len(texto_pagina) < 100: 
                        continue

                    # Filtro 2: Saltar páginas de metadatos o legales
                    if i < 20 and any(key in texto_pagina.upper() for key in SKIP_KEYWORDS):
                        logger.info(f"   ⏩ Saltando página {i+1} (Contenido no técnico detectado)")
                        continue

                    # Fragmentación del texto para el RAG
                    fragmentos = text_splitter.split_text(texto_pagina)

                    for idx, txt in enumerate(fragmentos):
                        # Limpieza de espacios múltiples y saltos de línea huérfanos
                        txt_limpio = re.sub(r'\s+', ' ', txt).strip()

                        todas_las_paginas_docs.append(
                            Document(
                                page_content=txt_limpio,
                                metadata={
                                    "source": archivo,
                                    "page": i + 1,
                                    "chunk_index": idx
                                }
                            )
                        )

                    # Batching para evitar saturar la memoria o la API
                    if len(todas_las_paginas_docs) >= 200:
                        vector_store.add_documents(todas_las_paginas_docs)
                        logger.info(f"   🚀 Indexados {len(todas_las_paginas_docs)} fragmentos de '{archivo}'...")
                        todas_las_paginas_docs = []

                # Subir fragmentos restantes
                if todas_las_paginas_docs:
                    vector_store.add_documents(todas_las_paginas_docs)
                    logger.info(f"   🚀 Finalizados fragmentos restantes de '{archivo}'.")

            logger.info(f"✨ Éxito total: {archivo} ha sido asimilado correctamente.")

        except Exception as e:
            logger.error(f"❌ Error crítico procesando {archivo}: {e}")

if __name__ == "__main__":
    logger.info("🔮 El Ojo comienza la lectura de los manuales sagrados...")
    procesar_manuales_por_pagina()
    logger.info("✅ Conocimiento almacenado correctamente en el plano vectorial.")