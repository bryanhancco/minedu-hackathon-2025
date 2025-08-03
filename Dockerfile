FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema mínimas
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Actualizar pip y copiar requirements
RUN pip install --upgrade pip

# Copiar e instalar dependencias Python en pasos separados para optimizar memoria
COPY requirements.txt .
RUN pip install --no-cache-dir gunicorn
RUN pip install --no-cache-dir -r requirements.txt --no-deps --force-reinstall

# Copiar código de la aplicación
COPY . .

# Exponer puerto
EXPOSE 8000

# Comando para ejecutar con gunicorn
CMD ["gunicorn", "--worker-tmp-dir", "/tmp", "--config", "gunicorn.config.py", "api.api:app"]
