# users-service/main.py
# Microservicio independiente de usuarios. Corre en el puerto 8001.
from fastapi import FastAPI

app = FastAPI(title="Users Service")

# TODO 1: lista "usuarios" en memoria
usuarios = [
    {"id": 1, "nombre": "Jorge"},
    {"id": 2, "nombre": "Juan"},
    {"id": 3, "nombre": "Maria"},
    {"id": 4, "nombre": "Laura"},
    {"id": 5, "nombre": "Carlos"},
    {"id": 6, "nombre": "Yedes"},
]


@app.get("/usuarios/{usuario_id}")
def obtener_usuario(usuario_id: int):
    # TODO 2: busca el usuario por id
    for usuario in usuarios:
        if usuario["id"] == usuario_id:
            return usuario
    return {"error": "no encontrado"}


@app.get("/usuarios")
def listar_usuarios():
    # TODO 3: retorna la lista completa
    return usuarios
