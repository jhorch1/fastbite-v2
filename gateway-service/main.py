# gateway-service/main.py
# API GATEWAY: unico punto de entrada al sistema (puerto 8000).
# Reenvia (proxy) cada peticion al microservicio correspondiente.
#
# Ejemplos (todo entra por el puerto 8000):
#   GET  http://localhost:8000/api/usuarios/usuarios        -> users-service  /usuarios
#   GET  http://localhost:8000/api/menu/menu/1              -> menu-service   /menu/1
#   POST http://localhost:8000/api/pedidos/pedidos          -> orders-service /pedidos

import os

from fastapi import FastAPI, Request, Response
import httpx

app = FastAPI(title="API Gateway - FastBite")

# TODO 1: diccionario con la URL base de cada microservicio.
# En local se usa localhost; dentro de Docker, docker-compose cambia estas
# variables por el nombre de cada servicio (ej. http://users-service:8001).
RUTAS = {
    "usuarios": os.getenv("USERS_SERVICE_URL", "http://localhost:8001"),
    "menu": os.getenv("MENU_SERVICE_URL", "http://localhost:8002"),
    "pedidos": os.getenv("ORDERS_SERVICE_URL", "http://localhost:8003"),
}


@app.get("/")
def inicio():
    return {"gateway": "FastBite", "servicios": list(RUTAS.keys()),
            "uso": "/api/{servicio}/{ruta}  ej: /api/menu/menu"}


@app.api_route("/api/{servicio}/{ruta_resto:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def gateway(servicio: str, ruta_resto: str, request: Request):
    # TODO 2: valida que "servicio" exista en RUTAS
    if servicio not in RUTAS:
        return {"error": "servicio no encontrado"}

    # TODO 3: construye la url destino
    url_destino = f"{RUTAS[servicio]}/{ruta_resto}"

    # TODO 4: reenvia la peticion con el mismo metodo HTTP y el mismo body
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            respuesta = await client.request(
                request.method,
                url_destino,
                params=request.query_params,
                content=await request.body(),
                headers={"Content-Type": request.headers.get("content-type", "application/json")},
            )
    except httpx.RequestError:
        return Response(
            content=f'{{"error": "{servicio} no disponible"}}',
            status_code=503,
            media_type="application/json",
        )

    # Se devuelve tal cual: mismo cuerpo y mismo codigo (201, 404, 402...)
    return Response(
        content=respuesta.content,
        status_code=respuesta.status_code,
        media_type=respuesta.headers.get("content-type", "application/json"),
    )
