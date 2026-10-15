import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
ORDERS_PATH = ROOT / "orders-service"
sys.path.insert(0, str(ORDERS_PATH))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"No se pudo cargar {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


users = load_module("fastbite_users_main", ROOT / "users-service" / "main.py")
menu = load_module("fastbite_menu_main", ROOT / "menu-service" / "main.py")
gateway = load_module("fastbite_gateway_main", ROOT / "gateway-service" / "main.py")
orders = load_module("fastbite_orders_main", ORDERS_PATH / "main.py")


class HttpErrorStatusTests(unittest.TestCase):
    def test_missing_user_returns_404_with_error_body(self):
        with TestClient(users.app) as client:
            response = client.get("/usuarios/999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"error": "Usuario no encontrado"})

    def test_missing_menu_product_returns_404_with_error_body(self):
        with TestClient(menu.app) as client:
            response = client.get("/menu/999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"error": "Producto no encontrado"})

    def test_unknown_gateway_service_returns_404_with_error_body(self):
        with TestClient(gateway.app) as client:
            response = client.get("/api/inexistente/recurso")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"error": "Servicio no encontrado"})

    def test_invalid_order_quantity_returns_400_with_clear_detail(self):
        with patch.object(
            orders,
            "consultar_servicio",
            return_value={"id": 1, "nombre": "Jorge"},
        ):
            with TestClient(orders.app) as client:
                response = client.post("/pedidos", json={
                    "usuario_id": 1,
                    "items": [{"producto_id": 1, "cantidad": 0}],
                    "metodo_pago": "efectivo",
                })

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {"detail": "La cantidad debe ser mayor que cero"},
        )


class CqrsIdTests(unittest.TestCase):
    def setUp(self):
        orders.pedidos.clear()
        orders.siguiente_id = 1
        orders.event_store.clear()

    def test_created_orders_and_cqrs_events_keep_the_same_ids(self):
        def consultar(url: str, _nombre: str):
            if "/usuarios/" in url:
                return {"id": 1, "nombre": "Jorge"}
            return {
                "id": 1,
                "nombre": "Hamburguesa clasica",
                "precio": 18000,
            }

        with patch.object(orders, "consultar_servicio", side_effect=consultar), \
                patch.object(orders, "publicar_evento"):
            with TestClient(orders.app) as client:
                respuestas = [
                    client.post("/pedidos", json={
                        "usuario_id": 1,
                        "items": [{"producto_id": 1, "cantidad": 1}],
                        "metodo_pago": "efectivo",
                    })
                    for _ in range(3)
                ]
                cancelacion = client.put(
                    "/pedidos/2/estado",
                    json={"estado": "cancelado"},
                )
                resumen = client.get("/pedidos/resumen")

        self.assertEqual([r.status_code for r in respuestas], [201, 201, 201])
        self.assertEqual([r.json()["pedido"]["id"] for r in respuestas], [1, 2, 3])
        self.assertEqual(cancelacion.status_code, 200)
        self.assertEqual(
            [e["datos"]["pedido_id"] for e in orders.event_store
             if e["tipo"] == "PedidoCreado"],
            [1, 2, 3],
        )
        self.assertEqual([pedido["id"] for pedido in resumen.json()], [1, 2, 3])
        self.assertEqual(
            [pedido["estado"] for pedido in resumen.json()],
            ["activo", "cancelado", "activo"],
        )

    def test_order_creation_survives_rabbitmq_failure(self):
        def consultar(url: str, _nombre: str):
            if "/usuarios/" in url:
                return {"id": 1, "nombre": "Jorge"}
            return {"id": 1, "nombre": "Hamburguesa clasica", "precio": 18000}

        with patch.object(orders, "consultar_servicio", side_effect=consultar), \
                patch.object(
                    orders,
                    "publicar_evento",
                    side_effect=OSError("broker unavailable"),
                ):
            with TestClient(orders.app) as client:
                response = client.post("/pedidos", json={
                    "usuario_id": 1,
                    "items": [{"producto_id": 1, "cantidad": 1}],
                    "metodo_pago": "efectivo",
                })

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["pedido"]["id"], 1)
        self.assertEqual(orders.event_store[0]["datos"]["pedido_id"], 1)


class RabbitMqPublisherTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module(
            "fastbite_eventos_test",
            ORDERS_PATH / "eventos.py",
        )

    def test_reuses_connection_and_closes_it_on_shutdown(self):
        class FakeChannel:
            is_open = True

            def __init__(self):
                self.messages = []

            def exchange_declare(self, **_kwargs):
                pass

            def basic_publish(self, **kwargs):
                self.messages.append(kwargs)

        class FakeConnection:
            is_open = True

            def __init__(self):
                self.fake_channel = FakeChannel()
                self.closed = False

            def channel(self):
                return self.fake_channel

            def close(self):
                self.closed = True
                self.is_open = False

        connection = FakeConnection()
        publisher = self.module.PublicadorEventos()
        with patch.object(
            self.module.pika,
            "BlockingConnection",
            return_value=connection,
        ) as connect:
            publisher.iniciar()
            publisher.publicar("PedidoCreado", {"pedido_id": 1})
            publisher.publicar("PedidoCreado", {"pedido_id": 2})
            publisher.cerrar()

        self.assertEqual(connect.call_count, 1)
        self.assertEqual(len(connection.fake_channel.messages), 2)
        self.assertTrue(connection.closed)

    def test_broker_failure_is_returned_to_caller(self):
        publisher = self.module.PublicadorEventos()
        with patch.object(
            self.module.pika,
            "BlockingConnection",
            side_effect=OSError("broker unavailable"),
        ):
            publisher.iniciar()
            with self.assertRaisesRegex(OSError, "broker unavailable"):
                publisher.publicar("PedidoCreado", {"pedido_id": 1})
            publisher.cerrar()


if __name__ == "__main__":
    unittest.main()
