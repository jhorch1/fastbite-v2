# orders-service/orders_service_cqrs_extension.py
# ESTE ARCHIVO SE INTEGRA AL orders-service YA EXISTENTE (Semana 3)
# Implementa CQRS (separa comandos de consultas) + Event Sourcing (el estado
# se reconstruye a partir de eventos, no se guarda directamente).

# TODO 1: lista global "event_store" que sera el almacen de eventos
event_store = []


def comando_crear_pedido(pedido_id: int, usuario: str, items: list):
    """
    LADO DEL COMANDO (escritura).
    En vez de guardar el pedido final directamente, se guarda un EVENTO.
    """
    # TODO 2: crea el evento
    evento = {
        "tipo": "PedidoCreado",
        "datos": {"pedido_id": pedido_id, "usuario": usuario, "items": items},
    }
    # TODO 3: agregalo a event_store
    event_store.append(evento)
    # TODO 4: retorna una confirmacion simple
    return {"status": "evento registrado"}


def comando_cancelar_pedido(pedido_id: int):
    """Otro comando: agrega un evento PedidoCancelado."""
    # TODO 5: agrega el evento PedidoCancelado
    event_store.append({"tipo": "PedidoCancelado", "datos": {"pedido_id": pedido_id}})
    return {"status": "evento registrado"}


def consulta_resumen_pedidos():
    """
    LADO DE LA CONSULTA (lectura).
    Reconstruye el estado actual RECORRIENDO (replaying) todos los eventos guardados.
    Este modelo de lectura es DISTINTO a como se guardaron los datos.
    """
    resumen = []
    # TODO 6: replay de eventos
    for evento in event_store:
        if evento["tipo"] == "PedidoCreado":
            resumen.append({
                "id": evento["datos"]["pedido_id"],
                "usuario": evento["datos"]["usuario"],
                "items": evento["datos"]["items"],
                "estado": "activo"
            })
        elif evento["tipo"] == "PedidoCancelado":
            pedido_id = evento["datos"]["pedido_id"]
            for pedido in resumen:
                if pedido["id"] == pedido_id:
                    pedido["estado"] = "cancelado"
    return resumen
