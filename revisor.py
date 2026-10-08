"""Revisor IA: controla las reglas de contenido que el validador en Python no puede ver."""
import json
import os

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

REVISOR_PROMPT = """Sos un QA senior que revisa archivos .feature generados por otra IA. \
Recibís la historia de usuario y el .feature. Tu tarea es encontrar errores de CONTENIDO \
según estas reglas:

- R02: los supuestos no se contradicen con los escenarios del archivo.
- R06: los Antecedentes valen para todos los escenarios y ningún escenario los contradice.
- R10: los pasos son declarativos (comportamiento), no describen la interfaz (botones, clics).
- R11: los pasos Cuando no incluyen precondiciones; esas van en un Dado.
- R12: cada criterio de aceptación de la historia tiene al menos un escenario.
- R14: las reglas con números se prueban en el límite, justo dentro y justo fuera.
- R21: el nombre de cada escenario describe lo que el escenario realmente prueba.
- R22: ningún paso es solo un parámetro (por ejemplo, "Entonces <resultado>").
- R23: no hay requisitos inventados (roles, pagos, etc.) que la historia no menciona.

Reportá solo violaciones claras. Si dudás, no lo reportes. Si no hay problemas, \
devolvé una lista vacía.

Gravedad:
- "alta": el escenario prueba algo incorrecto, contradice la historia o falta cobertura.
- "baja": estilo o mejora menor.

Respondé SOLO con JSON válido, sin texto adicional y sin ```, con este formato:
{"problemas": [{"regla": "R11", "gravedad": "alta", "detalle": "Línea 34: ..."}]}
"""


def extraer_json(texto):
    """Toma el primer objeto JSON del texto, aunque venga con texto o ``` alrededor."""
    inicio, fin = texto.find("{"), texto.rfind("}")
    if inicio == -1 or fin == -1:
        raise ValueError("La respuesta del revisor no contiene JSON")
    return json.loads(texto[inicio:fin + 1])


def revisar(historia, feature):
    """Devuelve la lista de problemas encontrados por el revisor IA."""
    cliente = Anthropic(timeout=120)
    respuesta = cliente.messages.create(
        model=os.environ["CLAUDE_MODEL"],
        max_tokens=8000,
        system=REVISOR_PROMPT,
        messages=[{
            "role": "user",
            "content": f"HISTORIA DE USUARIO:\n{historia}\n\nARCHIVO .feature:\n{feature}",
        }],
    )
    texto = "".join(b.text for b in respuesta.content if b.type == "text")
    return extraer_json(texto).get("problemas", [])
