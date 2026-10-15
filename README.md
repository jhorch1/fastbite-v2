# FastBite v2 – Microservicios con FastAPI

Sistema de pedidos de comida construido por semanas en el curso de Arquitectura de Software:

| Semana | Tema | Dónde está |
|---|---|---|
| 2 | Microservicios que se comunican por HTTP + **Microkernel** (plugins de pago) | `users-service`, `menu-service`, `orders-service/plugins` |
| 3 | **Coreografía** con RabbitMQ (eventos) | `orders-service/eventos.py`, `notifications-service` |
| 4 | **API Gateway**, **Docker** y **CQRS + Event Sourcing** | `gateway-service`, `docker/`, `orders-service/orders_service_cqrs_extension.py` |

## Arquitectura

```
                     ┌──────────────────────┐
   Cliente ────────► │ gateway-service :8000│  (único punto de entrada)
                     └──────────┬───────────┘
          ┌─────────────────────┼─────────────────────┐
          ▼                     ▼                     ▼
 users-service :8001   menu-service :8002   orders-service :8003 ── plugins de pago
                                ▲                     │            (efectivo, tarjeta, nequi)
                                └──── HTTP ───────────┤
                                                      │ publica "PedidoCreado"
                                                      ▼
                                              RabbitMQ :5672
                                                      │
                                                      ▼
                                      notifications-service (escucha eventos)
```

---

## Opción 1: con Docker (recomendada)

**Requisito:** tener [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado y abierto (debe decir *Engine running*).

```powershell
git clone https://github.com/jhorch1/fastbite-v2.git
cd fastbite-v2/docker
docker compose up --build
```

En Windows también puedes hacer **doble clic en `iniciar-docker.bat`**.

La primera vez tarda unos minutos (descarga Python y RabbitMQ). Está listo cuando aparecen:
```
notifications-service-1  | Esperando eventos... (Ctrl+C para salir)
gateway-service-1        | Uvicorn running on http://0.0.0.0:8000
```

Para detenerlo: `Ctrl + C`, o `docker compose down` desde la carpeta `docker`.

## Opción 2: sin Docker (Python local)

Requiere Python 3.10 o superior y RabbitMQ corriendo (por ejemplo:
`docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management`).

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r users-service/requirements.txt -r menu-service/requirements.txt -r orders-service/requirements.txt -r gateway-service/requirements.txt -r notifications-service/requirements.txt
.\iniciar.ps1
```
`iniciar.ps1` abre una ventana por servicio.

---

## URLs

| Qué | URL |
|---|---|
| **API Gateway (Swagger)** | http://localhost:8000/docs |
| Users service | http://localhost:8001/docs |
| Menu service | http://localhost:8002/docs |
| Orders service | http://localhost:8003/docs |
| Panel de RabbitMQ (guest / guest) | http://localhost:15672 |

Por el gateway, las rutas son `/api/{servicio}/{ruta}`:

| Petición | Va a |
|---|---|
| `GET /api/usuarios/usuarios` | users-service `/usuarios` |
| `GET /api/menu/menu` | menu-service `/menu` |
| `POST /api/pedidos/pedidos` | orders-service `/pedidos` |

## Prueba rápida

1. Crear un pedido: `POST http://localhost:8000/api/pedidos/pedidos`
   ```json
   {
     "usuario_id": 1,
     "items": [ { "producto_id": 1, "cantidad": 2 }, { "producto_id": 6, "cantidad": 2 } ],
     "metodo_pago": "nequi"
   }
   ```
   Respuesta: `{"pedido": {...total 44000, pago aprobado...}, "cqrs": {"status": "evento registrado"}}`
2. Ver la notificación en los logs de `notifications-service`:
   `NOTIFICACION: Hola Jorge (usuario 1), tu pedido #1 por $44000 (nequi) fue creado con exito.`
3. CQRS: `GET /api/pedidos/pedidos/resumen` (estado reconstruido) y `GET /api/pedidos/pedidos/eventos` (event store).
   Cada evento `PedidoCreado` conserva el ID asignado al pedido; el publicador reutiliza
   una conexión RabbitMQ durante la vida del servicio y la cierra al apagarlo.

## Endpoints principales de orders-service

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/pedidos` | Crea un pedido: valida usuario y productos por HTTP, cobra con un plugin, publica `PedidoCreado` y registra el evento CQRS |
| GET | `/pedidos` | Lista los pedidos |
| GET | `/pedidos/{id}` | Ver un pedido |
| PUT | `/pedidos/{id}/estado` | Cambia el estado: `creado → en_preparacion → listo → entregado`, o `cancelado` |
| GET | `/pedidos/resumen` | **CQRS (consulta):** estado reconstruido recorriendo los eventos |
| GET | `/pedidos/eventos` | El *event store* tal cual |
| GET | `/metodos-pago` | Plugins de pago cargados automáticamente |

**Códigos de error:** 400 (método de pago no soportado o transición de estado inválida), 402 (pago rechazado: no se crea el pedido), 404 (usuario, producto o pedido no existe), 503 (un servicio está apagado).

## Agregar un método de pago (Microkernel)

No se toca el núcleo (`main.py`). Solo se crea `orders-service/plugins/pago_<nombre>.py` con una función:

```python
def procesar(monto: float) -> dict:
    return {"metodo": "<nombre>", "monto": monto, "estado": "aprobado"}
```

El núcleo lo descubre al arrancar y aparece en `GET /metodos-pago`.

## Problemas comunes

| Problema | Solución |
|---|---|
| `failed to connect to the docker API ... dockerDesktopLinuxEngine` | Abre Docker Desktop y espera a que diga *Engine running*. |
| `port is already allocated` (5672, 8000–8003) | Algo ya usa ese puerto: detén el contenedor `rabbitmq` suelto (`docker stop rabbitmq`) o cierra las ventanas de `iniciar.ps1`. |
| `AMQPConnectionError` en los logs de notifications al arrancar | Normal: RabbitMQ tarda en encender. El contenedor se reinicia solo y luego muestra `Esperando eventos...`. |
| Hice cambios en el código y no se ven | Reconstruye: `docker compose up --build`. |

> Los datos (usuarios, menú, pedidos y eventos) están en memoria: se reinician al reiniciar los servicios.
