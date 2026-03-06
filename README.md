# 👁️ The Eye of Lisary: Multi-Agent RAG Backend
"Un artefacto digital de sabiduría infinita para directores de juego y arquitectos de héroes."  Este repositorio contiene exclusivamente el Core Backend del sistema. Está diseñado como una API robusta y agnóstica que utiliza LangChain y Fireworks AI para procesar la lógica de Dungeons & Dragons 5e.

## 🏗️ Arquitectura General (Backend-Only)
El sistema opera bajo un modelo de Micro-Agentes Especialistas orquestados por un clasificador de intenciones (Router). La arquitectura está totalmente desacoplada para permitir una integración flexible con cualquier frontend (Web, Discord o Móvil).

## 📂 Estructura Detallada de Carpetas

``` Plaintext
the-eye-of-lisary-backend/
├── data/
│   ├── manuales/           # PDFs Oficiales (PHB, DMG, Tasha, Xanathar)
│   └── vector_store/       # Base de datos vectorial persistent(ChromaDB)
├── src/
│   ├── main.py             # Entry point: FastAPI, Middleware y CORS
│   ├── core/               # LA COLUMNA VERTEBRAL (Singletons y Abstracciones)
│   │   ├── config.py       # Pydantic Settings para .env y constantes
│   │   ├── factory.py      # Generador de modelos Fireworks (Llama-3 8B/70B)
│   │   ├── memory.py       # Manejo de hilos de conversación y persistencia de sesión
│   │   └── base_agent.py   # Clase abstracta (Interface) para estandarizar especialistas
│   ├── agents/             # LOS ESPECIALISTAS (Capa de Razonamiento)
│   │   ├── router.py       # El "Ojo" Admin: Clasifica la consulta y deriva al experto
│   │   ├── rules_expert.py # Especialista en RAW, Lógica Física y Problemáticas de mesa
│   │   ├── char_builder.py # Experto en Fichas, Subclases y progresión de niveles
│   │   └── spell_mentor.py # Mentor de magia, combinaciones y optimización de conjuros
│   ├── tools/              # LAS ACCIONES (Capa de Ejecución)
│   │   ├── rag_tool.py     # Lógica de consulta a la Vector DB (Chroma)
│   │   ├── wiki_tool.py    # Conector con Tavily para Wikidot y DanWiki
│   │   └── sheet_manager.py# Motor de cálculo de estadísticas y guardado de JSON
│   └── database/           # INFRAESTRUCTURA DE DATOS
│       ├── vector_engine.py# Configuración de Embeddings (HuggingFace locales)
│       └── ingesta.py      # Script de segmentación (Chunking) y carga de manuales
├── .env.example            # Plantilla de variables de entorno
├── requirements.txt        # Dependencias de Python
└── README.md
```

### 🛠️ Especificaciones Técnicas
1. Capa Core (Proceso On-Demand)
El backend es Stateless. Cada petición activa un flujo de trabajo que carga la memoria de la sesión específica, consulta las herramientas necesarias y cierra el proceso al entregar la respuesta, optimizando el uso de recursos y tokens.

2. RAG Híbrido (Local + Web)
El sistema utiliza un sistema de recuperación dual. Si el especialista no encuentra una regla específica en los manuales locales o busca contenido de comunidad, utiliza el agente de búsqueda para consultar Wikidot y DanWiki en tiempo real.

3. Lógica de Agentes (ReAct)
Utilizamos el framework ReAct (Reasoning + Acting). Los especialistas no solo responden; primero generan un "Pensamiento" (Thought), deciden una "Acción" (Action), observan el resultado de la herramienta (Observation) y finalmente entregan la "Respuesta Final".

## 🚀 Guía de Inicio para el Desarrollador
Requisitos
Python 3.10+

Clave de API de Fireworks.ai

Clave de API de Tavily (Búsqueda Web)

Instalación y Configuración
Clonar el repositorio: git clone https://github.com/haiiro1/the-eye-of-lisary-backend.git

Crear un entorno virtual: 
``` cmd
python -m venv venv
```

Instalar dependencias:
``` cmd
pip install -r requirements.txt
```
Ingesta de datos:

Coloca tus archivos PDF en data/manuales/.

Ejecuta:
``` cmd
python src/database/ingesta.py para construir la base de datos vectorial.
```
## 📡 Integración con Frontend (En dearrollo)
Este backend expone una API REST profesional. Al estar en repositorios separados, se recomienda configurar un cliente HTTP (como Axios o Fetch) en el frontend apuntando al endpoint de consulta.

``` json
// Ejemplo de Request
POST /api/v1/consultar
{
  "session_id": "mesa_01_user_42",
  "query": "Como Druida nivel 3, ¿qué subclases de Tasha me recomiendas?"
}
```