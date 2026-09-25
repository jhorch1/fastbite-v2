# orders-service/main.py
# Microservicio de pedidos. Corre en el puerto 8003.
# Ahora se comunica por HTTP con users-service (8001) y menu-service (8002),
# y usa un sistema de PLUGINS para procesar pagos (patron Microkernel).

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

# TODO 1: importa los plugins de pago
# from plugins import pago_efectivo, pago_tarjeta

app = FastAPI(title="Orders Service")

USERS_SERVICE_URL = "http://localhost:8001"
MENU_SERVICE_URL = "http://localhost:8002"

pedidos = []
siguiente_id = 1

# TODO 2: crea el diccionario PLUGINS que mapea el nombre del metodo de pago
# a la funcion procesar() de cada plugin, ej:
# PLUGINS = {"efectivo": pago_efectivo.procesar, "tarjeta": pago_tarjeta.procesar}
PLUGINS = {}


class ItemPedido(BaseModel):
    producto_id: int
    cantidad: int


class NuevoPedido(BaseModel):
    usuario_id: int
    items: list[ItemPedido]
    metodo_pago: str


@app.post("/pedidos")
def crear_pedido(pedido: NuevoPedido):
    global siguiente_id

    # TODO 3: valida que el usuario existe llamando por HTTP a users-service
    # usando httpx.get(f"{USERS_SERVICE_URL}/usuarios/{pedido.usuario_id}")
    # Si la respuesta trae {"error": ...}, lanza HTTPException(404, "Usuario no encontrado")

    # TODO 4: para cada item, valida que el producto existe llamando a menu-service
    # usando httpx.get(f"{MENU_SERVICE_URL}/menu/{item.producto_id}")

    # TODO 5: valida que pedido.metodo_pago exista en PLUGINS.
    # Si no existe: raise HTTPException(400, "Metodo de pago no soportado")

    # TODO 6: calcula el monto total (puedes usar un valor fijo simple para simplificar)
    # y llama a PLUGINS[pedido.metodo_pago](monto_total) para procesar el pago

    # TODO 7: crea el diccionario del pedido con id, usuario_id, items, metodo_pago,
    # resultado del pago y estado "creado"; agregalo a la lista "pedidos";
    # incrementa siguiente_id; retorna el pedido creado
    pass


@app.get("/pedidos")
def listar_pedidos():
    return pedidos
