# 🧠 Agents Module: Capa de Razonamiento

Este directorio es el centro de inteligencia de **The Eye of Lisary**. Utiliza una arquitectura de **Multi-Agentes Especialistas** orquestada mediante un grafo de estados (**LangGraph**). El sistema no responde de forma lineal; analiza la intención del usuario y deriva la consulta al experto (o expertos) más capacitados para la tarea.

## 🏗️ Arquitectura del Grafo (`graph.py`)

El flujo de trabajo se basa en un ciclo de razonamiento y acción:

1.  **Router Node**: El punto de entrada. Clasifica la consulta y decide qué agentes deben activarse.
2.  **Orchestrator**: Una función lógica que gestiona la cola de agentes (`selected_agents`) y dirige el flujo al siguiente nodo correspondiente.
3.  **Specialist Nodes**: Nodos que ejecutan la lógica específica (Reglas, Hechizos, Construcción, etc.).
4.  **Aggregator**: Si varios agentes intervinieron, este nodo combina las respuestas en una sola salida coherente y natural.

## 👥 Los Especialistas

### 1. `router.py` (El Clasificador)
Es el "Ojo" administrativo. No responde la pregunta, sino que identifica intenciones como:
* `rules`: Consultas sobre mecánicas o leyes físicas del juego.
* `spells`: Dudas sobre magia, componentes o efectos de área.
* `builder`: Creación de personajes, dotes y niveles.
* `web`: Necesidad de buscar información externa en Wikidot o DanWiki.

### 2. `rules_expert.py` (Especialista en RAW)
Se encarga de interpretar las reglas oficiales (*Rules As Written*).
* **Herramientas**: Utiliza el RAG para consultar los manuales PDF indexados.
* **Enfoque**: Resolución de conflictos en mesa y aclaración de mecánicas de combate o entorno.

### 3. `spell_mentor.py` (Mentor de Magia)
Especializado exclusivamente en el tejido de la magia.
* **Función**: Optimización de conjuros, aclaración de niveles de lanzamiento y combinaciones tácticas.

### 4. `char_builder.py` (Arquitecto de Héroes)
Ayuda en la progresión técnica del personaje.
* **Contexto**: Utiliza la información de la ficha cargada (`sheet_context`) para dar consejos personalizados de nivel subida o elección de subclases.

### 5. `web_omni_expert.py` (Investigador)
Se activa cuando la información no está en los manuales locales o se busca contenido de la comunidad (*homebrew*).
* **Herramientas**: Conecta con la `wiki_tool` para navegar por internet en tiempo real.

### 6. `chat_expert.py` (Interacción Social)
Maneja la conversación general, saludos o preguntas que no requieren datos técnicos de D&D.

## 🔄 Lógica de ReAct (Reasoning + Acting)
Cada agente (exceptuando el de chat) sigue el patrón **ReAct**:
* **Pensamiento (Thought)**: El agente explica internamente por qué necesita una herramienta.
* **Acción (Action)**: Ejecuta una consulta a la base de datos o web.
* **Observación (Observation)**: Analiza el resultado obtenido.
* **Respuesta (Final Answer)**: Entrega la solución final al usuario.
