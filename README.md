# 👁️ The Eye of Lisary: Multi-Agent RAG Backend
"Un artefacto digital de sabiduría infinita para directores de juego y arquitectos de héroes."

Este repositorio contiene exclusivamente el **Core Backend** del sistema. Está diseñado como una API robusta y agnóstica que utiliza **LangGraph**, **LangChain** y **Fireworks AI** para procesar la lógica de Dungeons & Dragons 5e.

## 🏗️ Arquitectura General
El sistema opera bajo un modelo de **Micro-Agentes Especialistas** orquestados por un clasificador de intenciones (Router). La arquitectura está totalmente desacoplada para permitir una integración flexible con cualquier frontend (Web, Discord o Móvil).

### Capas del Sistema:
1.  **Capa Core**: Gestiona la fábrica de modelos, configuraciones de entorno y la persistencia de hilos de conversación.
2.  **Capa de Agentes**: Especialistas en reglas, conjuros, construcción de personajes y búsqueda web que utilizan la lógica **ReAct** (Reasoning + Acting).
3.  **Capa de Herramientas**: Conectores para RAG local, búsquedas en tiempo real (Tavily y ddg) y procesamiento de fichas PDF.
4.  **Capa de Datos**: Motores de búsqueda vectorial (ChromaDB) e historial de conversaciones en SQLite.

## 📂 Estructura del Proyecto

* [**`src/core/`**](src/core/README.md): Singletons, fábrica de modelos (`factory.py`) y manejo de memoria.
* [**`src/agents/`**](src/agents/README.md): Definición del Grafo (`graph.py`), router de intenciones y nodos especialistas.
* [**`src/tools/`**](src/tools/README.md): Herramientas de RAG, conectores web y gestión de fichas PDF.
* [**`src/database/`**](src/database/README.md): Motor de vectores, ingesta de manuales y persistencia.
* [**`docker/`**](docker/README.md): Configuración de contenedores y orquestación con Docker Compose.


## 🛠️ Especificaciones Técnicas
* **Modelos**: Optimizado para **Qwen2-8B** (Razonamiento) y **Qwen2-8B** (Ruteo/Chat rápido) vía Fireworks AI.
* **Embeddings**: Utiliza `nomic-ai/nomic-embed-text-v1.5` para la búsqueda semántica.
* **RAG Híbrido**: Si la regla no aparece en los manuales locales, el sistema consulta fuentes externas en tiempo real.

## 🚀 Guía de Inicio

### Requisitos Previos
* Python 3.12+ (para instalación venv).
* Docker y Docker Compose (para instalación con contenedores).
* Claves de API de **Fireworks.ai** y **Tavily**.

---

### Opción A: Instalación con Virtual Environment (venv)
Ideal para desarrollo rápido y depuración local.

1.  **Clonar e instalar dependencias**:
    ```bash
    git clone [https://github.com/haiiro1/the-eye-of-lisary-backend.git](https://github.com/haiiro1/the-eye-of-lisary-backend.git)
    cd the-eye-of-lisary-backend
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```
2.  **Configurar Entorno**: Copia `.env.example` a `.env` y rellena tus credenciales.
3.  **Ingesta de Manuales**: Coloca tus PDFs en `data/manuales/` y ejecuta:
    ```bash
    python src/database/ingesta.py
    ```
4.  **Ejecutar**: `python src/main.py`.

---

### Opción B: Instalación con Docker
Ideal para entornos productivos y consistencia entre servicios.

1.  **Configurar Entorno**: Asegúrate de que el archivo `.env` en la raíz tenga las claves necesarias.
2.  **Levantar Servicios**: Desde la raíz del proyecto, ejecuta:
    ```bash
    docker-compose up --build -d
    ```
3.  **Verificación**: El backend estará disponible en `http://localhost:8000` y el frontend en `http://localhost:8501`.

---

## 📡 Integración API
```json
POST /chat
{
  "session_id": "mesa_dnd_01",
  "message": "¿Qué conjuros de nivel 1 me recomiendas para un bardo?"
}