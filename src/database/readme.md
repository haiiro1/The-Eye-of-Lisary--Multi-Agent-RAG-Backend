# 🗄️ Database Module: Infraestructura de Datos

Este directorio gestiona el ciclo de vida de la información en **The Eye of Lisary**, desde la ingesta de manuales físicos (PDF) hasta la persistencia de las conversaciones en tiempo real.

## 🗂️ Componentes del Módulo

### 1. `vector_engine.py` (Motor de Búsqueda Semántica)
Es el núcleo de la recuperación de información. Configura cómo el sistema "entiende" y busca en los manuales.
* **Embeddings**: Utiliza el modelo `nomic-ai/nomic-embed-text-v1.5` a través de Fireworks AI para convertir texto en vectores matemáticos.
* **ChromaDB**: Gestiona la base de datos vectorial local donde se almacenan estos vectores para búsquedas de similitud de coseno.
* **Singleton**: Garantiza que el modelo de embeddings y la conexión a la base de datos se carguen una sola vez para optimizar recursos.

### 2. `ingesta.py` (Procesador de Manuales)
Script encargado de transformar documentos estáticos en conocimiento utilizable.
* **Segmentación (Chunking)**: Divide los PDFs de la carpeta `data/manuales/` en fragmentos manejables para que el modelo pueda citar secciones específicas.
* **Carga**: Indexa estos fragmentos en ChromaDB, permitiendo que el `rag_tool` encuentre respuestas rápidamente.

### 3. `persistence.py` (Memoria a Largo Plazo)
Maneja el guardado del estado del grafo de agentes.
* **Checkpointer**: Utiliza una base de datos SQLite (`data/chat_history.db`) para registrar cada paso del razonamiento y los mensajes intercambiados.
* **Recuperación**: Permite que, si el servidor se reinicia, los usuarios puedan continuar sus consultas exactamente donde las dejaron mediante su `session_id`.

## 🏗️ Flujo de Datos

1.  **Ingesta**: El desarrollador coloca PDFs en `data/manuales/` y ejecuta `ingesta.py`.
2.  **Indexación**: El texto se convierte en vectores y se guarda en `data/vector_store/`.
3.  **Consulta**: Cuando un agente necesita una regla, `vector_engine.py` busca los fragmentos más parecidos a la duda del usuario.
4.  **Persistencia**: Cada interacción se graba en el historial para mantener la coherencia de la campaña.

## 🛠️ Mantenimiento

* **Actualizar Manuales**: Para añadir libros nuevos (como *Tasha's Cauldron of Everything*), simplemente agrégalos a la carpeta de datos y vuelve a ejecutar el script de ingesta.
* **Limpieza de Memoria**: El archivo `chat_history.db` puede ser auditado para revisar el rendimiento de los agentes o limpiar sesiones antiguas.