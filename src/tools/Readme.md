# 🛠️ Tools Module: Capa de Ejecución

Este directorio contiene las "manos" de los agentes. Mientras que los agentes se encargan de razonar, las **Tools** son funciones específicas que les permiten buscar información, procesar documentos o realizar cálculos técnicos de D&D 5e.

## 🗂️ Herramientas Principales

### 1. `rag_tool.py` (Consulta de Manuales)
Es el puente entre el razonamiento del agente y el conocimiento oficial almacenado en los manuales PDF.
* **Funcionamiento**: Realiza búsquedas semánticas en la base de datos vectorial (ChromaDB) para encontrar reglas, descripciones de monstruos o dotes.
* **Uso**: El `rules_expert` y el `spell_mentor` la utilizan para fundamentar sus respuestas en el contenido oficial (PHB, DMG, etc.).

### 2. `wiki_tool.py` (Búsqueda Web en Tiempo Real)
Extiende el conocimiento del sistema más allá de los archivos locales utilizando la API de **Tavily**.
* **Fuentes**: Está configurada para priorizar sitios de confianza de la comunidad como *D&D Beyond*, *Wikidot* y *DanWiki*.
* **Caso de uso**: Se activa cuando el usuario pregunta por contenido de suplementos nuevos o material *Homebrew* (creado por la comunidad) que no está en la base de datos local.

### 3. `sheet_manager.py` (Gestión de Fichas de Personaje)
Permite que el sistema entienda el contexto actual de los jugadores.
* **Procesamiento de PDF**: Utiliza un motor de extracción para leer los campos de formularios (widgets) en fichas de personaje de D&D 5e.
* **Formateo de Contexto**: Transforma los datos crudos del PDF en un resumen legible que se inyecta en el `sheet_context` del estado del agente.
* **Cálculos**: Incluye lógica para interpretar estadísticas, niveles y habilidades del personaje.

## ⚙️ Integración con los Agentes

Las herramientas no se ejecutan solas; están integradas en los nodos de los especialistas dentro de `src/agents/nodes.py`. Cada herramienta sigue el patrón de diseño de **LangChain**, lo que permite:

1.  **Auto-descripción**: Las herramientas tienen descripciones claras para que el LLM sepa cuándo es apropiado usarlas.
2.  **Manejo de Errores**: Si una búsqueda falla, la herramienta devuelve un mensaje de error que el agente puede interpretar para intentar una estrategia diferente.