# --- ETAPA 1: Builder ---
FROM python:3.12-slim AS builder

WORKDIR /app

# Evitamos archivos .pyc y habilitamos logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

#instalamos lo estrictamente necesario para compilar (ej. para psutil o drivers de DB)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# COPIAR SOLO requirements.txt PRIMERO (Clave para la caché de Docker)
COPY requirements.txt .

# Instalamos las librerías en el sistema del builder directamente
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# --- ETAPA 2: Runtime ---
FROM python:3.12-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app"

# Instalamos curl una sola vez aquí
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiamos LAS LIBRERÍAS ya instaladas desde el builder (site-packages de 3.12)
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# COPIAMOS EL CÓDIGO AL FINAL
# (Así, si cambias el código, Docker NO vuelve a instalar las librerías)
COPY . .

# Configuración de usuario no-root
RUN addgroup --system appgroup && adduser --system --group appuser \
    && chown -R appuser:appgroup /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]