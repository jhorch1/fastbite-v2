# Dockerfile de orders-service (mismo patron que docker/Dockerfile.orders-service)
FROM python:3.11-slim

WORKDIR /app

# TODO 1: copia el archivo de dependencias primero (aprovecha el cache de Docker)
COPY requirements.txt .

# TODO 2: instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# TODO 3: copia el resto del codigo del servicio
COPY . .

# TODO 4: expone el puerto en el que corre este servicio
EXPOSE 8003

# TODO 5: comando de arranque
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
