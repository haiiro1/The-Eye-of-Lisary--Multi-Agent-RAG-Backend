import os
import fitz
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from src.database.vector_engine import VectorEngine
from src.core.config import settings

def limpiar_texto(texto):
    texto = texto.replace('\x00', '')
    # Arreglo las palabras que quedan cortadas por el salto de línea del PDF
    texto = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', texto)
    # Quito saltos de línea excesivos para que el texto fluya mejor
    texto = re.sub(r'\n+', '\n', texto)
    return texto.strip()

def procesar_manuales_optimizado():
    if not os.path.exists(settings.MANUALS_PATH):
        os.makedirs(settings.MANUALS_PATH, exist_ok=True)

    vector_store = VectorEngine.get_vector_store()

    # Bajo el chunk_size a 800; me di cuenta que así recupera info más precisa
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=120,
        separators=["\n### ", "\n## ", "\n# ", "\n\n", "\n", " "]
    )

    SKIP_KEYWORDS = ["CRÉDITOS", "AGRADECIMIENTOS", "BIBLIOGRAFÍA", "ÍNDICE"]
    archivos_pdf = [f for f in os.listdir(settings.MANUALS_PATH) if f.endswith('.pdf')]

    for archivo in archivos_pdf:
        path = os.path.join(settings.MANUALS_PATH, archivo)
        print(f"📄 Procesando: {archivo}")

        try:
            with fitz.open(path) as doc:
                docs_a_indexar = []

                for i, pagina in enumerate(doc):
                    texto_raw = pagina.get_text("text")
                    texto_limpio = limpiar_texto(texto_raw)

                    # Ignoro páginas vacías o con paja (créditos, intros, etc.)
                    if len(texto_limpio) < 150: continue
                    if any(key in texto_limpio.upper() for key in SKIP_KEYWORDS) and i < 15:
                        continue

                    fragmentos = text_splitter.split_text(texto_limpio)

                    for idx, txt in enumerate(fragmentos):
                        # Le meto el origen al texto para que el modelo no alucine la fuente
                        contenido_con_contexto = f"[Manual: {archivo}, Pág: {i+1}]\n{txt}"

                        docs_a_indexar.append(
                            Document(
                                page_content=contenido_con_contexto,
                                metadata={
                                    "source": archivo,
                                    "page": i + 1,
                                    "chunk": idx
                                }
                            )
                        )

                    # Subo de a 100 para que no se me cuelgue la memoria
                    if len(docs_a_indexar) >= 100:
                        vector_store.add_documents(docs_a_indexar)
                        docs_a_indexar = []

                if docs_a_indexar:
                    vector_store.add_documents(docs_a_indexar)

            print(f"✨ Listo: {archivo}")

        except Exception as e:
            print(f"❌ Falló {archivo}: {e}")

if __name__ == "__main__":
    # Acuérdate de borrar la carpeta vector_store si vas a re-indexar todo
    procesar_manuales_optimizado()