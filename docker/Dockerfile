# Imagen inmutable por seguridad
FROM python:3.10-slim

WORKDIR /app

# Instalación de dependencias del sistema
#'curl' es para el healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia de requerimientos y optimización de cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Definición del HEALTHCHECK
# --interval: cada cuánto tiempo se ejecuta (30s)
# --timeout: cuánto espera antes de considerar que falló (5s)
# --start-period: tiempo de gracia al iniciar el contenedor (5s)
# --retries: fallos permitidos antes de marcar como 'unhealthy' (3)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]