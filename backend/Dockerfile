# --- ETAPA 1: CONSTRUCCIÓN (BUILDER) ---
FROM python:3.12-slim

# Establecemos el directorio de trabajo dentro del contenedor
WORKDIR /app

# 1. ¡INSTALAR DEPENDENCIAS DE COMPILACIÓN!
# Python Slim (Debian) necesita estos paquetes para instalar dependencias binarias como pandas y numpy
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiamos el archivo de dependencias
COPY ./requirements.txt /app/

# 2. Instalamos las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto de la aplicación
COPY . /app

# Comando de ejecución (asumiendo que usas uvicorn)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]