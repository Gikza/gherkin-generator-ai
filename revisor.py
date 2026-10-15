"""Revisor IA: controla las reglas de contenido que el validador en Python no puede ver."""
import json
import os

from anthropic import Anthropic
from dotenv import load_dotenv

import uso

from prompt import CRITERIO_LONGITUD, CRITERIO_PERMISOS

load_dotenv()

REVISOR_PROMPT = f"""Sos un QA senior que revisa archivos .feature generados por otra IA. \
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

Permisos: {CRITERIO_PERMISOS} Si la historia restringe el acceso, los escenarios de rol \
denegado, acceso por URL directa y usuario sin sesión son obligatorios: NO los marques como \
R23 ni como R10. Si la historia no restringe el acceso, esos escenarios SÍ son R23.

Longitud: {CRITERIO_LONGITUD} Si la historia define un máximo y falta probarlo en el límite, es \
R14. Si no lo define y el archivo prueba (o supone) un máximo, es R23. Un comentario \
"# Pregunta abierta" sobre la longitud es correcto: no lo marques.

Reportá solo violaciones claras. Si dudás, no lo reportes. Si no hay problemas, \
devolvé una lista vacía.

Gravedad:
- "alta": el escenario prueba algo incorrecto, contradice la historia o falta cobertura.
- "baja": estilo o mejora menor.

Respondé SOLO con JSON válido, sin texto adicional y sin ```, con este formato:
{{"problemas": [{{"regla": "R11", "gravedad": "alta", "detalle": "Línea 34: ..."}}]}}
"""


# La gravedad la decide Python, no la IA, para que sea siempre la misma.
# "alta" = se pide corregir. "baja" = se muestra como sugerencia.
GRAVEDAD_POR_REGLA = {
    "R02": "alta",  # supuestos que contradicen el archivo
    "R06": "alta",  # Antecedentes contradictorios
    "R11": "alta",  # precondición dentro de un Cuando
    "R12": "alta",  # criterio sin cobertura
    "R14": "alta",  # faltan valores límite
    "R21": "alta",  # el nombre no coincide con lo que se prueba
    "R22": "alta",  # paso que es solo un parámetro
    "R23": "alta",  # requisito inventado
    "R10": "baja",  # estilo declarativo: el revisor a veces se equivoca acá
}


def aplicar_gravedad(problemas, tabla=GRAVEDAD_POR_REGLA):
    """Reemplaza la gravedad que propuso la IA por la de la tabla fija."""
    for problema in problemas:
        problema["gravedad"] = tabla.get(problema.get("regla"), "baja")
    return problemas


def extraer_json(texto):
    """Toma el primer objeto JSON del texto, aunque venga con texto o ``` alrededor."""
    inicio, fin = texto.find("{"), texto.rfind("}")
    if inicio == -1 or fin == -1:
        raise ValueError("La respuesta del revisor no contiene JSON")
    return json.loads(texto[inicio:fin + 1])


def revisar(entrada, salida, prompt=REVISOR_PROMPT, tabla=GRAVEDAD_POR_REGLA,
            etiquetas=("HISTORIA DE USUARIO", "ARCHIVO .feature")):
    """Devuelve la lista de problemas encontrados por el revisor IA.

    Por defecto revisa casos Gherkin; para reportes de bugs se le pasan
    otro prompt, otra tabla de gravedad y otras etiquetas.
    """
    cliente = Anthropic(timeout=120)
    respuesta = cliente.messages.create(
        model=os.environ["CLAUDE_MODEL"],
        max_tokens=8000,
        system=prompt,
        messages=[{
            "role": "user",
            "content": f"{etiquetas[0]}:\n{entrada}\n\n{etiquetas[1]}:\n{salida}",
        }],
    )
    uso.registrar(respuesta)
    texto = "".join(b.text for b in respuesta.content if b.type == "text")
    return aplicar_gravedad(extraer_json(texto).get("problemas", []), tabla)
