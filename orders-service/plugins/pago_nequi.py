# plugins/pago_nequi.py
# Plugin nuevo: pago con Nequi.
# No se edito el nucleo (main.py): el nucleo lo descubre solo porque
# el archivo se llama pago_*.py y tiene la funcion procesar(monto).

import random

NOMBRE = "nequi"          # nombre con el que se elige en el pedido: "metodo_pago": "nequi"
LIMITE_POR_PAGO = 2_000_000


def procesar(monto: float) -> dict:
    if monto > LIMITE_POR_PAGO:
        return {
            "metodo": NOMBRE,
            "monto": monto,
            "estado": "rechazado",
            "motivo": f"Nequi no permite pagos mayores a {LIMITE_POR_PAGO}",
        }
    return {
        "metodo": NOMBRE,
        "monto": monto,
        "estado": "aprobado",
        "referencia": f"NEQ-{random.randint(100000, 999999)}",
    }
