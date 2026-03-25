# 🐳 Docker Infrastructure

Este directorio contiene toda la configuración necesaria para desplegar **The Eye of Lisary** utilizando contenedores. La arquitectura está diseñada para separar el motor de IA (Backend) de la interfaz de usuario (Frontend), permitiendo un escalado independiente y una configuración de red segura.

## 🏗️ Composición del Sistema

El despliegue se gestiona a través de **Docker Compose**, que orquesta dos servicios principales:

### 1. Backend (`eye-of-lisary-backend`)
* **Imagen**: Basada en `python:3.10-slim`.
* **Puerto**: `8000`.
* **Responsabilidad**: Expone la API de FastAPI, gestiona los agentes de LangGraph y conecta con las bases de datos vectoriales.
* **Persistencia**: Monta volúmenes para `./data` (manuales y DB) y `./src` (código fuente), permitiendo que los cambios en la lógica de los agentes se reflejen en tiempo real sin reiniciar el contenedor.
* **Healthcheck**: Incluye una verificación automática que consulta el endpoint `/health` para asegurar que el motor de IA esté listo antes de permitir conexiones del frontend.

### 2. Frontend (`eye-of-lisary-frontend`)
* **Puerto**: `8501`.
* **Responsabilidad**: Proporciona la interfaz de usuario (Streamlit/Web).
* **Dependencia**: Está configurado para esperar a que el backend reporte un estado "saludable" (`service_healthy`) antes de iniciar.

## 🛠️ Archivos de Configuración

* **`docker-compose.yml`**: El orquestador que define las redes, volúmenes, límites de memoria (2G para el backend) y variables de entorno.
* **`Dockerfile`**: Define la construcción de la imagen del backend, instalando las dependencias de `requirements.txt` y configurando el entorno de ejecución de Python.
* **`Dockerfile.frontend`**: Define la construcción de la capa de presentación.

## 🚀 Instrucciones de Despliegue

Para levantar toda la infraestructura, ejecuta el siguiente comando desde la *raiz/docker*:

```bash
docker-compose -f docker/docker-compose.yml up --build -d