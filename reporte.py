"""Reportes de bugs: arma la entrada y usa el mismo ciclo que los casos Gherkin."""
from functools import partial

from generador import ciclo_de_revision, corregir, llamar_generador
from reporte_prompt import GRAVEDAD_REPORTE, REPORTE_PROMPT, REVISOR_REPORTE_PROMPT
from reporte_validador import validar_reporte
from revisor import revisar


# Tipos de archivo que se aceptan como evidencia y cómo se nombran en el reporte.
EXTENSIONES_ADJUNTO = {
    "png": "captura", "jpg": "captura", "jpeg": "captura", "gif": "captura", "webp": "captura",
    "mp4": "video", "webm": "video", "mov": "video",
}


def tipo_de_adjunto(nombre):
    """"captura" o "video" según la extensión del archivo."""
    return EXTENSIONES_ADJUNTO.get(nombre.rsplit(".", 1)[-1].lower(), "archivo")


def armar_entrada(descripcion, log="", adjuntos=()):
    """Une la descripción del QA, el log y los nombres de los adjuntos en un solo texto para la IA.

    De los adjuntos solo se envía el NOMBRE: la IA no ve las imágenes ni los videos.
    """
    entrada = f"Descripción del QA:\n{descripcion.strip()}"
    if log.strip():
        entrada += f"\n\nLog o error de consola:\n{log.strip()}"
    if adjuntos:
        lineas = "\n".join(f"- {tipo_de_adjunto(n)}: {n}" for n in adjuntos)
        entrada += f"\n\nAdjuntos aportados por el QA (la IA no ve su contenido):\n{lineas}"
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
