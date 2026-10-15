# Dockerfile de notifications-service: no es una API HTTP, es un consumidor de RabbitMQ.
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Sin EXPOSE: no recibe peticiones, solo escucha eventos.
# -u = salida sin buffer, para ver las notificaciones al instante en "docker compose logs"
CMD ["python", "-u", "main.py"]
