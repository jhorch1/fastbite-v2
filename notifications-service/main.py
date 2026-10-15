# notifications-service/main.py
# Microservicio de notificaciones (patron Coreografia).
# No tiene API HTTP y nadie lo llama: escucha los eventos que publica
# orders-service en RabbitMQ y reacciona notificando al usuario.
import os
import pika
import json

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")   # en Docker: "rabbitmq"
EXCHANGE = "fastbite_eventos"


def callback(ch, method, properties, body):
    evento = json.loads(body)

    # TODO 1: si el evento es "PedidoCreado", imprimir el mensaje de notificacion
    if evento["tipo"] == "PedidoCreado":
        d = evento["datos"]
        print(f"NOTIFICACION: Hola {d['usuario']} (usuario {d['usuario_id']}), "
              f"tu pedido #{d['pedido_id']} por ${d['total']} ({d['metodo_pago']}) fue creado con exito.",
              flush=True)


def main():
    # TODO 2: abrir la conexion con RabbitMQ
    conexion = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))

    # TODO 3: crear un canal
    canal = conexion.channel()

    # TODO 4: declarar el mismo exchange que usa el publicador
    canal.exchange_declare(exchange=EXCHANGE, exchange_type="fanout")

    # TODO 5: crear una cola temporal (nombre aleatorio, se borra al cerrar este servicio)
    resultado = canal.queue_declare(queue="", exclusive=True)
    nombre_cola = resultado.method.queue

    # TODO 6: enlazar la cola al exchange
    canal.queue_bind(exchange=EXCHANGE, queue=nombre_cola)

    # TODO 7: consumir los mensajes de la cola
    canal.basic_consume(queue=nombre_cola, on_message_callback=callback, auto_ack=True)
    print("Esperando eventos... (Ctrl+C para salir)", flush=True)
    canal.start_consuming()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("notifications-service detenido.")
