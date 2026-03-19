import os
import fitz
import re # Para limpieza de texto
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from src.database.vector_engine import VectorEngine
from src.core.config import settings

def procesar_manuales_por_pagina():
    if not os.path.exists(settings.MANUALS_PATH):
        os.makedirs(settings.MANUALS_PATH, exist_ok=True)

    vector_store = VectorEngine.get_vector_store()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150, 
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    # PALABRAS CLAVE PARA OMITIR PÁGINAS NO RELEVANTES
    SKIP_KEYWORDS = ["CRÉDITOS", "AGRADECIMIENTOS", "BIBLIOGRAFÍA", "LITERATURA INSPIRADORA", "ÍNDICE"]

    archivos_pdf = [f for f in os.listdir(settings.MANUALS_PATH) if f.endswith('.pdf')]

    for archivo in archivos_pdf:
        path = os.path.join(settings.MANUALS_PATH, archivo)
        print(f"📄 Procesando: {archivo}")

        try:
            with fitz.open(path) as doc:
                todas_las_paginas_docs = [] # Acumulador para batching

                for i, pagina in enumerate(doc):
                    texto_raw = pagina.get_text("text")
                    texto_pagina = texto_raw.replace('\x00', '').strip()

                    # 🎯 FILTRO 1: Páginas casi vacías
                    if len(texto_pagina) < 100: 
                        continue

                    # 🎯 FILTRO 2: Saltar páginas de créditos/intro (opcional pero recomendado)
                    if any(key in texto_pagina.upper() for key in SKIP_KEYWORDS) and i < 20:
                        print(f"   ⏩ Saltando página {i+1} (Posible contenido no técnico)")
                        continue

                    fragmentos = text_splitter.split_text(texto_pagina)

                    docs_pagina = [
                        Document(
                            page_content=txt,
                            metadata={
                                "source": archivo,
                                "page": i + 1,
                                "chunk_index": idx
                            }
                        )
                        for idx, txt in enumerate(fragmentos)
                    ]

                    todas_las_paginas_docs.extend(docs_pagina)

                    # Subir cada 50 páginas para no saturar ni perder progreso
                    if len(todas_las_paginas_docs) > 200:
                        vector_store.add_documents(todas_las_paginas_docs)
                        print(f"   🚀 Indexadas {len(todas_las_paginas_docs)} fragmentos...")
                        todas_las_paginas_docs = []

                # Subir el remanente
                if todas_las_paginas_docs:
                    vector_store.add_documents(todas_las_paginas_docs)

            print(f"✨ Finalizado con éxito: {archivo}\n")

        except Exception as e:
            print(f"❌ Error procesando {archivo}: {e}")

if __name__ == "__main__":
    # RECOMENDACIÓN: Borrar chroma_db antes si cambiaste el modelo de embeddings
    procesar_manuales_por_pagina()