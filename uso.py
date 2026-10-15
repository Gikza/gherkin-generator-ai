"""Cuenta cuántas llamadas y tokens gasta la herramienta (lo usa evaluar.py).

generador.py y revisor.py registran cada respuesta de la API acá.
"""
_uso = {"llamadas": 0, "tokens_entrada": 0, "tokens_salida": 0}


def registrar(respuesta):
    """Suma el uso de una respuesta de la API. Si no trae datos de uso, solo cuenta la llamada."""
    uso = getattr(respuesta, "usage", None)
    _uso["llamadas"] += 1
    _uso["tokens_entrada"] += getattr(uso, "input_tokens", 0) or 0
    _uso["tokens_salida"] += getattr(uso, "output_tokens", 0) or 0


def reiniciar():
    for clave in _uso:
        _uso[clave] = 0


def leer():
    """Copia del uso acumulado desde el último reiniciar()."""
    return dict(_uso)
