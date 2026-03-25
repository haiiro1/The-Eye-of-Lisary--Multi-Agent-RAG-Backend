# 🗂️ Core 

Este directorio contiene los componentes fundacionales de **The Eye of Lisary**. Su objetivo es proporcionar una infraestructura robusta, validada y escalable que permita la interacción entre los modelos de lenguaje (LLM), la memoria de sesión y la lógica de Dungeons & Dragons 5e.

## 🗂️ Estructura de Archivos

### 1. `base_agent.py` (Interfaz de Agentes)
Define la clase abstracta `BaseAgent` que sirve como contrato para todos los especialistas.
* **Propósito**: Garantiza que cada experto (Reglas, Conjuros, Constructor) implemente los métodos necesarios para razonar y ejecutar herramientas.
* **Abstracción**: Permite que el sistema sea extensible; añadir un nuevo experto solo requiere heredar de esta clase.

### 2. `config.py` (Gestión de Entorno)
Centraliza la configuración del sistema utilizando `pydantic-settings`.
* **Validación**: Comprueba al inicio que existan las claves de API necesarias (`FIREWORKS_API_KEY`, `TAVILY_API_KEY`) y las rutas de base de datos.
* **Seguridad**: Gestiona las variables del archivo `.env` de forma tipada y segura.

### 3. `factory.py` (Generador de LLMs)
Implementa el patrón *Factory* para la instanciación de modelos en Fireworks AI.
* **Especialización**: Configura modelos de "Razonamiento" (Llama-3 70B/Qwen) para tareas complejas y modelos de "Ruteo" (Llama-3 8B) para clasificación rápida.
* **Control**: Gestiona parámetros técnicos como `temperature`, `max_tokens` y `stop_tokens` para evitar respuestas truncadas o alucinaciones de formato.

### 4. `state.py` (Definición del Estado)
Define el objeto `AgentState`, el esquema de datos fundamental que fluye a través del grafo de LangGraph.
* **Contenido**: Mantiene el historial de mensajes, el contexto de la ficha del personaje cargada, el idioma de la sesión y la cola de agentes pendientes por actuar.

### 5. `memory.py` (Persistencia de Sesión)
Gestiona la capacidad del sistema para recordar interacciones pasadas.
* **Hilos de Conversación**: Utiliza un `thread_id` para aislar las conversaciones de diferentes usuarios o mesas de juego.
* **Conectividad**: Se integra con el checkpointer de la base de datos para recuperar el estado exacto del chat tras un reinicio.

### 6. `callbacks.py` & `logging_config.py`
* **Monitoreo**: `callbacks.py` integra **Langfuse** para el rastreo de trazas, permitiendo auditar el razonamiento interno de los agentes y el consumo de tokens.
* **Observabilidad**: `logging_config.py` estandariza los registros del sistema, facilitando la depuración en entornos de producción.