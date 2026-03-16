import os
import fitz
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from src.database.vector_engine import VectorEngine
from src.core.config import settings

def procesar_manuales_por_pagina():
    # Conexión al motor de vectores configurado en vector_engine.py
    vector_store = VectorEngine.get_vector_store()

    # Configuración del splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, # Tamaño menor para que quepan varios por página
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " "]
    )

    archivos_pdf = [f for f in os.listdir(settings.MANUALS_PATH) if f.endswith('.pdf')]

    for archivo in archivos_pdf:
        path = os.path.join(settings.MANUALS_PATH, archivo)
        print(f"📄 Procesando archivo: {archivo}")

        try:
            with fitz.open(path) as doc:
                for i, pagina in enumerate(doc):
                    # Extraer texto de la página actual
                    texto_pagina = pagina.get_text("text").replace('\x00', '').strip()

                    if len(texto_pagina) < 10: # Omitir páginas casi vacías
                        continue

                    # Dividir el texto de ESTA página en fragmentos
                    fragmentos = text_splitter.split_text(texto_pagina)

                    # Crear documentos con metadatos de página para verificación
                    docs_pagina = [
                        Document(
                            page_content=txt,
                            metadata={
                                "source": archivo,
                                "page": i + 1,  # Guardamos el número de página
                                "chunk_index": idx
                            }
                        )
                        for idx, txt in enumerate(fragmentos)
                    ]

                    if docs_pagina:
                        vector_store.add_documents(docs_pagina)
                        print(f"  ✅ Página {i+1}: {len(docs_pagina)} fragmentos indexados.")

            print(f"✨ Finalizado: {archivo}\n")

        except Exception as e:
            print(f"❌ Error en {archivo}: {e}")

if __name__ == "__main__":
    procesar_manuales_por_pagina()