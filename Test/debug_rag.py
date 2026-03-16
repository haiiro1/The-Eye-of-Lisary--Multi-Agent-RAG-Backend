import os
import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from src.database.vector_engine import VectorEngine
from src.core.config import settings

def procesar_manuales_por_pagina():
    # Obtenemos el vector store
    vector_store = VectorEngine.get_vector_store()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " "]
    )

    # Listar archivos PDF en la ruta configurada
    archivos_pdf = [f for f in os.listdir(settings.MANUALS_PATH) if f.endswith('.pdf')]

    for archivo in archivos_pdf:
        path = os.path.join(settings.MANUALS_PATH, archivo)
        print(f"📄 Procesando: {archivo}")

        try:
            with fitz.open(path) as doc:
                for i, pagina in enumerate(doc):
                    # Extraer texto de la página actual
                    texto_pagina = pagina.get_text("text").replace('\x00', '').strip()

                    if len(texto_pagina) < 20: # Ignorar páginas vacías
                        continue

                    # Fragmentar el texto de la página
                    fragmentos = text_splitter.split_text(texto_pagina)

                    # Crear documentos con metadato de página
                    docs_pagina = [
                        Document(
                            page_content=txt,
                            metadata={
                                "source": archivo,
                                "page": i + 1  # Guardamos el número de página
                            }
                        )
                        for txt in fragmentos
                    ]

                    if docs_pagina:
                        vector_store.add_documents(docs_pagina)
                        print(f"  ✅ Página {i+1} indexada ({len(docs_pagina)} fragmentos).")

        except Exception as e:
            print(f"❌ Error en {archivo}: {e}")

if __name__ == "__main__":
    procesar_manuales_por_pagina()