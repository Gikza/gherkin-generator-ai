"""Modo demo: muestra resultados REALES de la IA, grabados antes con evaluar.py --guardar-demo.

Sirve para publicar la app sin clave de la API (por ejemplo, en Streamlit Community Cloud):
no hace llamadas a la IA, así que no gasta créditos. Solo funcionan los ejemplos grabados.
"""
import json
from pathlib import Path

EJEMPLOS = Path(__file__).resolve().parent / "demo" / "ejemplos.json"

MENSAJE_SIN_EJEMPLO = (
    "En la demo solo funcionan los ejemplos grabados (elegí uno de la lista). "
    "Para usar la IA con tus propias historias o bugs, corré la herramienta en tu compu: "
    "las instrucciones están en el repositorio."
)


class SinEjemploGrabado(Exception):
    """La entrada no coincide con ningún ejemplo grabado."""


def cargar_ejemplos(ruta=EJEMPLOS):
    """Lista de ejemplos grabados. Vacía si todavía no se grabaron."""
    if not Path(ruta).exists():
        return []
    return json.loads(Path(ruta).read_text(encoding="utf-8"))["ejemplos"]


def ejemplos_de(tipo, ejemplos=None):
    """Ejemplos de un tipo: "gherkin" o "reporte"."""
    return [e for e in (cargar_ejemplos() if ejemplos is None else ejemplos) if e["tipo"] == tipo]


def _normalizar(texto):
    return " ".join(texto.split())


def buscar(entrada, tipo, ejemplos=None):
    """Devuelve el resultado grabado para esa entrada, o lanza SinEjemploGrabado."""
    for ejemplo in ejemplos_de(tipo, ejemplos):
        if _normalizar(ejemplo["entrada"]) == _normalizar(entrada):
            return ejemplo["resultado"]
    raise SinEjemploGrabado(MENSAJE_SIN_EJEMPLO)


def generar_con_revision(historia, avisar=lambda mensaje: None):
    """Misma firma que generador.generar_con_revision."""
    avisar("Modo demo: resultado real de la IA, grabado previamente")
    return buscar(historia, "gherkin")


def generar_reporte_con_revision(entrada, avisar=lambda mensaje: None):
    """Misma firma que reporte.generar_reporte_con_revision."""
    avisar("Modo demo: resultado real de la IA, grabado previamente")
    return buscar(entrada, "reporte")
