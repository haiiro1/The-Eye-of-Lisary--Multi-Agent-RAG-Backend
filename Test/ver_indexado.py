from src.database.vector_engine import VectorEngine

def inspeccionar_fragmentos(limit=10):
    # Obtenemos la conexión a Chroma
    vector_store = VectorEngine.get_vector_store()

    # Obtenemos los datos de la colección
    datos = vector_store.get()

    total = len(datos['ids'])
    if total == 0:
        print("⚠️ La base de datos está vacía. Ejecuta primero la ingesta.")
        return

    print(f"\n🔍 Total de fragmentos indexados: {total}")
    print(f"📋 Mostrando los últimos {min(limit, total)} fragmentos:\n")

    for i in range(min(limit, total)):
        idx = total - 1 - i
        contenido_crudo = datos['documents'][idx]
        metadatos = datos['metadatas'][idx]

        # Limpiamos los saltos de línea fuera del f-string para evitar el SyntaxError
        contenido_limpio = contenido_crudo[:150].replace('\n', ' ')

        print(f"--- Fragmento ID: {datos['ids'][idx]} ---")
        print(f"📄 Fuente: {metadatos.get('source', 'N/A')}")
        print(f"📖 Página: {metadatos.get('page', 'N/A')}")
        print(f"📝 Contenido: {contenido_limpio}...")
        print("-" * 40)

if __name__ == "__main__":
    inspeccionar_fragmentos()