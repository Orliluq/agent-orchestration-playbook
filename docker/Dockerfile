FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar dependencias y instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Exponer puerto para métricas/monitoring
EXPOSE 8000

# Variables de entorno para configuración
ENV PYTHONPATH=/app
ENV LOG_LEVEL=INFO

# Comando por defecto para ejecutar ejemplos
CMD ["python", "-m", "examples.invoice_ingest.run"]