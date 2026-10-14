"""Une la historia de usuario con las respuestas a las preguntas de aclaración.

No llama a la IA: solo arma el texto que se envía en la nueva generación.
Así se puede testear con pytest sin gastar créditos.
"""
import re

SIN_RESPUESTA = "(sin respuesta)"

# Una pregunta por línea, numerada: "1. ¿...?" o "1) ¿...?"
_PREGUNTA = re.compile(r"^\s*\d+[.)]\s*(.+?)\s*$")


def separar_preguntas(texto):
    """Devuelve la lista de preguntas (sin el número) a partir del texto de la IA."""
    preguntas = []
    for linea in texto.splitlines():
        coincidencia = _PREGUNTA.match(linea)
        if coincidencia:
            preguntas.append(coincidencia.group(1))
    return preguntas


def hay_respuestas(respuestas):
    """True si al menos una respuesta tiene texto."""
    return any(r.strip() for r in respuestas)


def armar_historia(historia, preguntas, respuestas):
    """Agrega a la historia una sección de aclaraciones con cada pregunta y su respuesta.

    Las preguntas sin responder quedan marcadas como SIN_RESPUESTA: el prompt le indica
    a la IA que tome un supuesto y lo anote, en lugar de volver a preguntar.
    """
    lineas = [historia.strip(), "", "Aclaraciones:"]
    for numero, (pregunta, respuesta) in enumerate(zip(preguntas, respuestas), start=1):
        lineas.append(f"{numero}. {pregunta}")
        lineas.append(f"   Respuesta: {respuesta.strip() or SIN_RESPUESTA}")
    return "\n".join(lineas)
