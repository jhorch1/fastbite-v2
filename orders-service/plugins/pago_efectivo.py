# plugins/pago_efectivo.py
# Un "plugin" de pago: una funcion independiente que el nucleo puede cargar sin conocerla de antemano.

def procesar(monto: float) -> dict:
    return {"metodo": "efectivo", "monto": monto, "estado": "aprobado"}
