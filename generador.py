"""Llama a la API de Claude: genera, revisa y corrige el .feature."""
import os

from anthropic import Anthropic
from dotenv import load_dotenv

from prompt import SYSTEM_PROMPT
from revisor import revisar
from validador import validar_texto

load_dotenv()

MAX_CORRECCIONES = 2  # decisión de la checklist: hasta 3 intentos en total


def limpiar_respuesta(texto):
    """Quita bloques de código (```) y espacios sobrantes, por si la IA los agrega."""
    lineas = [l for l in texto.strip().splitlines() if not l.strip().startswith("```")]
    return "\n".join(lineas).strip()


def interpretar(texto):
    """Clasifica la respuesta: preguntas de aclaración o archivo .feature."""
    texto = limpiar_respuesta(texto)
    if texto.startswith("PREGUNTAS"):
        preguntas = texto.split("\n", 1)[1].strip() if "\n" in texto else ""
        return {"tipo": "preguntas", "contenido": preguntas}
    return {"tipo": "feature", "contenido": texto + "\n"}


def llamar_generador(mensajes):
    """Hace una llamada al generador con la conversación indicada."""
    cliente = Anthropic(timeout=120)  # usa ANTHROPIC_API_KEY del .env
    respuesta = cliente.messages.create(
        model=os.environ["CLAUDE_MODEL"],
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        messages=mensajes,
    )
    # La respuesta puede incluir bloques de razonamiento: nos quedamos con el texto.
    texto = "".join(b.text for b in respuesta.content if b.type == "text")
    return interpretar(texto)


def generar(historia):
    """Primera generación a partir de la historia."""
    return llamar_generador([{"role": "user", "content": historia}])


def corregir(historia, feature, problemas):
    """Pide al generador que corrija su .feature según la lista de problemas."""
    lista = "\n".join(f"- {p['regla']}: {p['detalle']}" for p in problemas)
    pedido = (
        "Revisá tu archivo. Se encontraron estos problemas:\n"
        f"{lista}\n\n"
        "Corregilos y respondé con el archivo .feature COMPLETO en el FORMATO B."
    )
    return llamar_generador([
        {"role": "user", "content": historia},
        {"role": "assistant", "content": feature},
        {"role": "user", "content": pedido},
    ])


def problemas_de_forma(feature):
    """Convierte las fallas del validador en Python al mismo formato que el revisor."""
    problemas = []
    for regla, errores in validar_texto(feature).items():
        for error in errores:
            # Si una regla no se pudo evaluar, no es culpa del .feature: no pedimos corregir.
            gravedad = "baja" if error.startswith("No se pudo evaluar") else "alta"
            problemas.append({"regla": regla, "gravedad": gravedad, "detalle": error})
    return problemas


def generar_con_revision(historia, avisar=lambda mensaje: None):
    """Genera, valida, revisa y corrige hasta MAX_CORRECCIONES veces.

    Devuelve un diccionario con el tipo de resultado, el .feature final,
    los problemas que quedaron y el historial de cada intento.
    """
    avisar("Generando escenarios...")
    resultado = generar(historia)
    if resultado["tipo"] == "preguntas":
        return resultado

    historial = []
    for intento in range(MAX_CORRECCIONES + 1):
        feature = resultado["contenido"]

        avisar(f"Intento {intento + 1}: validando y revisando...")
        try:
            contenido = revisar(historia, feature)
            revisor_ok = True
        except ValueError:
            contenido, revisor_ok = [], False  # el revisor no devolvió JSON válido

        problemas = problemas_de_forma(feature) + contenido
        graves = [p for p in problemas if p.get("gravedad") == "alta"]
        historial.append({"intento": intento + 1, "problemas": problemas})

        if not graves or intento == MAX_CORRECCIONES:
            break

        avisar(f"Corrigiendo {len(graves)} problema(s) (corrección {intento + 1} de {MAX_CORRECCIONES})...")
        nuevo = corregir(historia, feature, graves)
        if nuevo["tipo"] != "feature":
            break  # si en vez de corregir devuelve preguntas, nos quedamos con la última versión
        resultado = nuevo

    return {
        "tipo": "feature",
        "contenido": feature,
        "problemas": problemas,
        "revisor_ok": revisor_ok,
        "historial": historial,
    }
