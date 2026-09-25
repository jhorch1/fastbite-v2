# users-service/main.py
# Microservicio independiente de usuarios. Corre en el puerto 8001.
from fastapi import FastAPI

app = FastAPI(title="Users Service")

# TODO 1: crea una lista "usuarios" en memoria con al menos 2 usuarios
# Ejemplo: {"id": 1, "nombre": "Juan"}
usuarios = [
    # TODO: agrega tus usuarios aqui
]

@app.get("/usuarios/{usuario_id}")
def obtener_usuario(usuario_id: int):
    # TODO 2: busca el usuario por id en la lista "usuarios" y retornalo
    # Si no existe, retorna un dict {"error": "no encontrado"} (por simplicidad en este ejercicio)
    pass

@app.get("/usuarios")
def listar_usuarios():
    # TODO 3: retorna la lista completa de usuarios
    pass
