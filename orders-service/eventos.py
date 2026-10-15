# orders-service/eventos.py
# Publicador de eventos (patron Coreografia).
# orders-service NO llama por HTTP al servicio de notificaciones: solo publica
# un evento en RabbitMQ y termina. Quien este suscrito reacciona por su cuenta.
import os
import pika
import json

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")   # en Docker: "rabbitmq"
EXCHANGE = "fastbite_eventos"


def publicar_evento(tipo_evento: str, datos: dict):
    # TODO 1: abrir la conexion con RabbitMQ
    conexion = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))

    # TODO 2: crear un canal sobre la conexion
    canal = conexion.channel()

    # TODO 3: declarar el exchange tipo "fanout" (reparte el mensaje a todas las colas enlazadas)
    canal.exchange_declare(exchange=EXCHANGE, exchange_type="fanout")

    # TODO 4: publicar el mensaje (evento en formato JSON)
    mensaje = {"tipo": tipo_evento, "datos": datos}
    canal.basic_publish(
        exchange=EXCHANGE,
        routing_key="",              # en fanout la routing key se ignora
        body=json.dumps(mensaje),
    )
    print(f"[eventos] Evento publicado: {tipo_evento} -> {datos}")

    # TODO 5: cerrar la conexion
    conexion.close()
