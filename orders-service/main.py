# orders-service/main.py
# Microservicio de pedidos. Corre en el puerto 8003.
# Se comunica por HTTP con users-service (8001) y menu-service (8002),
# y usa un sistema de PLUGINS para procesar pagos (patron Microkernel).

import os
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

import importlib
import pkgutil

# TODO 1: plugins de pago.
# El nucleo NO los importa uno por uno: los descubre solo dentro de la carpeta plugins/.
import plugins

# Publicador de eventos hacia RabbitMQ (coreografia)
from eventos import publicar_evento

# CQRS + Event Sourcing (Semana 4)
from orders_service_cqrs_extension import (
    comando_crear_pedido,
    comando_cancelar_pedido,
    consulta_resumen_pedidos,
    event_store,
)

app = FastAPI(title="Orders Service")

# En local: localhost. En Docker, docker-compose las cambia por el nombre del servicio.
USERS_SERVICE_URL = os.getenv("USERS_SERVICE_URL", "http://localhost:8001")
MENU_SERVICE_URL = os.getenv("MENU_SERVICE_URL", "http://localhost:8002")

pedidos = []
siguiente_id = 1

# TODO 2: diccionario PLUGINS (nombre del metodo -> funcion procesar del plugin)
# Patron Microkernel: el nucleo carga automaticamente todo archivo plugins/pago_*.py
# que tenga una funcion procesar(monto). Para agregar un metodo de pago nuevo
# solo se crea el archivo del plugin; este archivo (el nucleo) no se toca.
def cargar_plugins() -> dict:
    encontrados = {}
    for modulo in pkgutil.iter_modules(plugins.__path__):
        if not modulo.name.startswith("pago_"):
            continue
        plugin = importlib.import_module(f"plugins.{modulo.name}")
        if not hasattr(plugin, "procesar"):
            continue
        # El nombre del metodo sale de la variable NOMBRE del plugin,
        # o del nombre del archivo: pago_efectivo.py -> "efectivo"
        nombre = getattr(plugin, "NOMBRE", modulo.name.removeprefix("pago_"))
        encontrados[nombre] = plugin.procesar
    return encontrados


PLUGINS = cargar_plugins()

# Ciclo de vida del pedido: desde cada estado, a cuales se puede pasar.
#   creado -> en_preparacion -> listo -> entregado
#   (creado o en_preparacion) -> cancelado
TRANSICIONES = {
    "creado": ["en_preparacion", "cancelado"],
    "en_preparacion": ["listo", "cancelado"],
    "listo": ["entregado"],
    "entregado": [],   # estado final
    "cancelado": [],   # estado final
}


class ItemPedido(BaseModel):
    producto_id: int
    cantidad: int


class NuevoPedido(BaseModel):
    usuario_id: int
    items: list[ItemPedido]
    metodo_pago: str


class CambioEstado(BaseModel):
    estado: str


def consultar_servicio(url: str, nombre_servicio: str) -> dict:
    """Llama por HTTP a otro microservicio. Si esta apagado, responde 503."""
    try:
        respuesta = httpx.get(url, timeout=5)
        return respuesta.json()
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail=f"{nombre_servicio} no disponible")


@app.post("/pedidos", status_code=201)
def crear_pedido(pedido: NuevoPedido):
    global siguiente_id

    # TODO 3: valida que el usuario existe (users-service)
    usuario = consultar_servicio(f"{USERS_SERVICE_URL}/usuarios/{pedido.usuario_id}", "users-service")
    if "error" in usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if not pedido.items:
        raise HTTPException(status_code=400, detail="El pedido debe tener al menos un producto")

    # TODO 4: valida cada producto (menu-service) y arma el detalle
    detalle = []
    monto_total = 0
    for item in pedido.items:
        if item.cantidad <= 0:
            raise HTTPException(status_code=400, detail="La cantidad debe ser mayor que cero")
        producto = consultar_servicio(f"{MENU_SERVICE_URL}/menu/{item.producto_id}", "menu-service")
        if "error" in producto:
            raise HTTPException(status_code=404, detail=f"Producto {item.producto_id} no encontrado")

        subtotal = producto["precio"] * item.cantidad
        monto_total += subtotal
        detalle.append({
            "producto_id": producto["id"],
            "nombre": producto["nombre"],
            "cantidad": item.cantidad,
            "subtotal": subtotal,
        })

    # TODO 5: valida el metodo de pago
    if pedido.metodo_pago not in PLUGINS:
        raise HTTPException(status_code=400, detail="Metodo de pago no soportado")

    # TODO 6: procesa el pago con el plugin correspondiente
    resultado_pago = PLUGINS[pedido.metodo_pago](monto_total)

    # Si el plugin rechaza el pago, el pedido NO se crea (402 = Payment Required).
    # El nucleo no sabe POR QUE se rechazo: eso lo decide cada plugin.
    if resultado_pago.get("estado") != "aprobado":
        raise HTTPException(
            status_code=402,
            detail={
                "mensaje": "Pago rechazado, el pedido no fue creado",
                "pago": resultado_pago,
            },
        )

    # TODO 7: crea y guarda el pedido
    nuevo = {
        "id": siguiente_id,
        "usuario_id": pedido.usuario_id,
        "usuario": usuario["nombre"],
        "items": detalle,
        "total": monto_total,
        "metodo_pago": pedido.metodo_pago,
        "pago": resultado_pago,
        "estado": "creado",
        "historial": [{"estado": "creado", "fecha": datetime.now().isoformat(timespec="seconds")}],
    }
    pedidos.append(nuevo)
    siguiente_id += 1

    # Coreografia: publicamos el evento y terminamos.
    # No sabemos (ni nos importa) quien escucha este evento.
    # Si RabbitMQ esta apagado, el pedido igual queda creado.
    try:
        publicar_evento("PedidoCreado", {
            "pedido_id": nuevo["id"],
            "usuario_id": nuevo["usuario_id"],
            "usuario": nuevo["usuario"],
            "total": nuevo["total"],
            "metodo_pago": nuevo["metodo_pago"],
        })
    except Exception as error:
        print(f"[eventos] No se pudo publicar PedidoCreado (RabbitMQ apagado?): {error!r}")
    # CQRS: ademas de crear el pedido, se registra el EVENTO PedidoCreado
    items_dict = [item.model_dump() for item in pedido.items]
    confirmacion = comando_crear_pedido(str(pedido.usuario_id), items_dict)

    return {"pedido": nuevo, "cqrs": confirmacion}


@app.get("/pedidos")
def listar_pedidos():
    return pedidos


@app.get("/metodos-pago")
def listar_metodos_pago():
    return {"metodos_disponibles": sorted(PLUGINS.keys())}


def buscar_pedido(pedido_id: int) -> dict:
    for pedido in pedidos:
        if pedido["id"] == pedido_id:
            return pedido
    raise HTTPException(status_code=404, detail="Pedido no encontrado")


# ===== CQRS: lado de la CONSULTA (lectura) =====
# (van antes de /pedidos/{pedido_id} para que "resumen" no se tome como un id)
@app.get("/pedidos/resumen")
def resumen_pedidos():
    """Estado reconstruido recorriendo event_store (replay de eventos)."""
    return consulta_resumen_pedidos()


@app.get("/pedidos/eventos")
def ver_eventos():
    """El event_store tal cual: la fuente de verdad."""
    return event_store


@app.get("/pedidos/{pedido_id}")
def ver_pedido(pedido_id: int):
    return buscar_pedido(pedido_id)


@app.put("/pedidos/{pedido_id}/estado")
def actualizar_estado(pedido_id: int, cambio: CambioEstado):
    pedido = buscar_pedido(pedido_id)
    actual = pedido["estado"]
    nuevo = cambio.estado

    if nuevo not in TRANSICIONES:
        raise HTTPException(status_code=400, detail=f"Estado '{nuevo}' no existe")

    permitidos = TRANSICIONES[actual]
    if nuevo not in permitidos:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede pasar de '{actual}' a '{nuevo}'. Permitidos: {permitidos or 'ninguno (estado final)'}",
        )

    pedido["estado"] = nuevo
    if nuevo == "cancelado":
        # CQRS: el cancelado tambien se registra como EVENTO
        comando_cancelar_pedido(pedido_id)
    pedido["historial"].append({"estado": nuevo, "fecha": datetime.now().isoformat(timespec="seconds")})
    return pedido
