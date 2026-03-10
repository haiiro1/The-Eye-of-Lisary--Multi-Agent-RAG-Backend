import os

from ddgs import results
from src.tools.rag_tool import RAGTool
from src.core.logging_config import logger

def test_manuals():
    print("\n--- 🔍 DIAGNÓSTICO DE RAG ---")

    # 1. Verificar si existe la base de datos
    db_path = "data/vector_store"
    if not os.path.exists(db_path) or not os.listdir(db_path):
        print("❌ ERROR: La carpeta 'data/vector_store' está vacía o no existe.")
        print("👉 Debes ejecutar tu script de ingesta de manuales primero.")
        return

    # 2. Intentar una búsqueda manual
    try:
        rag = RAGTool()
        query = "Bola de Fuego"
        # Forzamos una búsqueda con k=5 para ver qué hay
        results = rag.search(query)

        if not results:
            print(f"❓ ChromaDB está activo pero no encontró nada para '{query}'.")
            print("👉 Esto sugiere que los PDFs no se leyeron correctamente.")
        else:
            print(f"✅ ¡Éxito! Se encontraron {len(results)} fragmentos.")
            # En debug_rag.py, dentro del bucle de impresión:
        for i, res in enumerate(results):
            print(f"📄 Fragmento {i+1} (Longitud: {len(res)} caracteres):")
            print(f"Contenido: '{res}'")
    except Exception as e:
        print(f"❌ Error al inicializar RAGTool: {e}")

if __name__ == "__main__":
    test_manuals()