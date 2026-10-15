# menu-service/main.py
# Microservicio independiente de menu. Corre en el puerto 8002.
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="Menu Service")

# TODO 1: lista "menu" de la Semana 1 (FastBite v1)
menu = [
    {"id": 1, "nombre": "Hamburguesa clasica", "categoria": "Comida", "precio": 18000},
    {"id": 2, "nombre": "Perro caliente", "categoria": "Comida", "precio": 12000},
    {"id": 3, "nombre": "Pizza personal", "categoria": "Comida", "precio": 15000},
    {"id": 4, "nombre": "Salchipapa", "categoria": "Comida", "precio": 14000},
    {"id": 5, "nombre": "Papas fritas", "categoria": "Acompanamiento", "precio": 7000},
    {"id": 6, "nombre": "Gaseosa", "categoria": "Bebida", "precio": 4000},
    {"id": 7, "nombre": "Jugo natural", "categoria": "Bebida", "precio": 6000},
    {"id": 8, "nombre": "Helado", "categoria": "Postre", "precio": 5000},
]


@app.get("/menu/{producto_id}")
def obtener_producto(producto_id: int):
    # TODO 2: busca el producto por id
    for producto in menu:
        if producto["id"] == producto_id:
            return producto
    return JSONResponse(
        status_code=404,
        content={"error": "Producto no encontrado"},
    )


@app.get("/menu")
def listar_menu():
    # TODO 3: retorna la lista completa del menu
    return menu
