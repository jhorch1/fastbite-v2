# Publicador de eventos (patron Coreografia).
# orders-service publica en RabbitMQ; los consumidores reaccionan de forma independiente.
import json
import logging
import os
import queue
import threading
from dataclasses import dataclass, field

import pika

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
EXCHANGE = "fastbite_eventos"
LOGGER = logging.getLogger(__name__)


@dataclass
class _Publicacion:
    mensaje: str
    finalizada: threading.Event = field(default_factory=threading.Event)
    error: Exception | None = None


class PublicadorEventos:
    """Mantiene una conexión RabbitMQ en un hilo propietario hasta el apagado."""

    def __init__(self):
        self._cola: queue.Queue[_Publicacion | None] = queue.Queue()
        self._hilo: threading.Thread | None = None
        self._ciclo_vida = threading.Lock()

    def iniciar(self) -> None:
        with self._ciclo_vida:
            if self._hilo is None or not self._hilo.is_alive():
                self._hilo = threading.Thread(
                    target=self._procesar_publicaciones,
                    name="fastbite-rabbitmq-publisher",
                    daemon=True,
                )
                self._hilo.start()

    def publicar(self, tipo_evento: str, datos: dict) -> None:
        mensaje = json.dumps({"tipo": tipo_evento, "datos": datos})
        publicacion = _Publicacion(mensaje)
        with self._ciclo_vida:
            if self._hilo is None or not self._hilo.is_alive():
                self._hilo = threading.Thread(
                    target=self._procesar_publicaciones,
                    name="fastbite-rabbitmq-publisher",
                    daemon=True,
                )
                self._hilo.start()
            self._cola.put(publicacion)

        publicacion.finalizada.wait()
        if publicacion.error is not None:
            raise publicacion.error
        print(f"[eventos] Evento publicado: {tipo_evento} -> {datos}")

    def cerrar(self) -> None:
        with self._ciclo_vida:
            hilo = self._hilo
            if hilo is None:
                return
            self._cola.put(None)
            hilo.join()
            self._hilo = None

    def _procesar_publicaciones(self) -> None:
        conexion = None
        canal = None
        try:
            while True:
                publicacion = self._cola.get()
                if publicacion is None:
                    break
                try:
                    if conexion is None or not conexion.is_open:
                        conexion = pika.BlockingConnection(
                            pika.ConnectionParameters(
                                host=RABBITMQ_HOST,
                                socket_timeout=5,
                                blocked_connection_timeout=5,
                            )
                        )
                        canal = conexion.channel()
                        canal.exchange_declare(
                            exchange=EXCHANGE,
                            exchange_type="fanout",
                        )

                    canal.basic_publish(
                        exchange=EXCHANGE,
                        routing_key="",
                        body=publicacion.mensaje,
                    )
                except Exception as error:
                    publicacion.error = error
                    if conexion is not None:
                        try:
                            if conexion.is_open:
                                conexion.close()
                        except (pika.exceptions.AMQPError, OSError):
                            LOGGER.exception("No se pudo cerrar la conexión RabbitMQ fallida")
                    conexion = None
                    canal = None
                finally:
                    publicacion.finalizada.set()
        finally:
            if conexion is not None and conexion.is_open:
                conexion.close()


_publicador = PublicadorEventos()


def iniciar_publicador() -> None:
    _publicador.iniciar()


def cerrar_publicador() -> None:
    _publicador.cerrar()


def publicar_evento(tipo_evento: str, datos: dict) -> None:
    _publicador.publicar(tipo_evento, datos)
