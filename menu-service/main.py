# menu-service/main.py
# Microservicio independiente de menu. Corre en el puerto 8002.
from fastapi import FastAPI

app = FastAPI(title="Menu Service")

# TODO 1: copia y pega aqui la lista "menu" que ya construiste en la Semana 1
menu = [
    # TODO: agrega tus productos aqui
]

@app.get("/menu/{producto_id}")
def obtener_producto(producto_id: int):
    # TODO 2: busca el producto por id. Si no existe, retorna {"error": "no encontrado"}
    pass

@app.get("/menu")
def listar_menu():
    # TODO 3: retorna la lista completa del menu
    pass
