"""Reportes de bugs: arma la entrada y usa el mismo ciclo que los casos Gherkin."""
from functools import partial

from generador import ciclo_de_revision, corregir, llamar_generador
from reporte_prompt import GRAVEDAD_REPORTE, REPORTE_PROMPT, REVISOR_REPORTE_PROMPT
from reporte_validador import validar_reporte
from revisor import revisar


def armar_entrada(descripcion, log=""):
    """Une la descripción del QA y el log (si hay) en un solo texto para la IA."""
    entrada = f"Descripción del QA:\n{descripcion.strip()}"
    if log.strip():
        entrada += f"\n\nLog o error de consola:\n{log.strip()}"
    return entrada


def generar_reporte(entrada):
    return llamar_generador([{"role": "user", "content": entrada}],
                            system=REPORTE_PROMPT, tipo="reporte")


corregir_reporte = partial(corregir, system=REPORTE_PROMPT, tipo="reporte",
                           formato="el reporte COMPLETO en el FORMATO B")

revisar_reporte = partial(revisar, prompt=REVISOR_REPORTE_PROMPT, tabla=GRAVEDAD_REPORTE,
                          etiquetas=("LO QUE CONTÓ EL QA", "REPORTE"))


def generar_reporte_con_revision(entrada, avisar=lambda mensaje: None):
    """Ciclo completo para reportes de bugs: generar, validar, revisar y corregir."""
    return ciclo_de_revision(
        entrada,
        generar_fn=generar_reporte,
        corregir_fn=corregir_reporte,
        revisar_fn=revisar_reporte,
        validar_fn=validar_reporte,
        tipo="reporte",
        avisar=avisar,
        que="el reporte",
    )
