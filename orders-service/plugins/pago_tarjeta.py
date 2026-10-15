# plugins/pago_tarjeta.py

def procesar(monto: float) -> dict:
    return {"metodo": "tarjeta", "monto": monto, "estado": "aprobado"}
