"""Llama a la API de Claude: genera, revisa y corrige (casos Gherkin y, con otros parámetros, reportes de bugs)."""
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


def interpretar(texto, tipo="feature"):
    """Clasifica la respuesta: preguntas de aclaración o el resultado pedido (tipo)."""
    texto = limpiar_respuesta(texto)
    if texto.startswith("PREGUNTAS"):
        preguntas = texto.split("\n", 1)[1].strip() if "\n" in texto else ""
        return {"tipo": "preguntas", "contenido": preguntas}
    return {"tipo": tipo, "contenido": texto + "\n"}


def llamar_generador(mensajes, system=SYSTEM_PROMPT, tipo="feature"):
    """Hace una llamada al generador con la conversación indicada."""
    cliente = Anthropic(timeout=120)  # usa ANTHROPIC_API_KEY del .env
    respuesta = cliente.messages.create(
        model=os.environ["CLAUDE_MODEL"],
        max_tokens=8000,
        system=system,
        messages=mensajes,
    )
    # La respuesta puede incluir bloques de razonamiento: nos quedamos con el texto.
    texto = "".join(b.text for b in respuesta.content if b.type == "text")
    return interpretar(texto, tipo)


def generar(historia):
    """Primera generación a partir de la historia."""
    return llamar_generador([{"role": "user", "content": historia}])


def corregir(entrada, salida, problemas, system=SYSTEM_PROMPT, tipo="feature",
             formato="el archivo .feature COMPLETO en el FORMATO B"):
    """Pide al generador que corrija su respuesta según la lista de problemas."""
    lista = "\n".join(f"- {p['regla']}: {p['detalle']}" for p in problemas)
    pedido = (
        "Revisá tu respuesta. Se encontraron estos problemas:\n"
        f"{lista}\n\n"
        f"Corregilos y respondé con {formato}."
    )
    return llamar_generador([
        {"role": "user", "content": entrada},
        {"role": "assistant", "content": salida},
        {"role": "user", "content": pedido},
    ], system=system, tipo=tipo)


def problemas_de_forma(texto, validar=validar_texto):
    """Convierte las fallas del validador en Python al mismo formato que el revisor."""
    problemas = []
    for regla, errores in validar(texto).items():
        for error in errores:
            # Si una regla no se pudo evaluar, no es culpa de la salida: no pedimos corregir.
            gravedad = "baja" if error.startswith("No se pudo evaluar") else "alta"
            problemas.append({"regla": regla, "gravedad": gravedad, "detalle": error})
    return problemas


def ciclo_de_revision(entrada, generar_fn, corregir_fn, revisar_fn, validar_fn,
                      tipo="feature", avisar=lambda mensaje: None, que="escenarios"):
    """Genera, valida, revisa y corrige hasta MAX_CORRECCIONES veces.

    Es el mismo ciclo para casos Gherkin y para reportes de bugs: cambian las
    funciones que se le pasan. Devuelve un diccionario con el tipo de resultado,
    la salida final, los problemas que quedaron y el historial de cada intento.
    """
    avisar(f"Generando {que}...")
    resultado = generar_fn(entrada)
    if resultado["tipo"] == "preguntas":
        return resultado

    historial = []
    for intento in range(MAX_CORRECCIONES + 1):
        salida = resultado["contenido"]

        avisar(f"Intento {intento + 1}: validando y revisando...")
        try:
            contenido = revisar_fn(entrada, salida)
            revisor_ok = True
        except ValueError:
            contenido, revisor_ok = [], False  # el revisor no devolvió JSON válido

        problemas = problemas_de_forma(salida, validar_fn) + contenido
        graves = [p for p in problemas if p.get("gravedad") == "alta"]
        historial.append({"intento": intento + 1, "problemas": problemas})

        if not graves or intento == MAX_CORRECCIONES:
            break

        avisar(f"Corrigiendo {len(graves)} problema(s) (corrección {intento + 1} de {MAX_CORRECCIONES})...")
        nuevo = corregir_fn(entrada, salida, graves)
        if nuevo["tipo"] != tipo:
            break  # si en vez de corregir devuelve preguntas, nos quedamos con la última versión
        resultado = nuevo

    return {
        "tipo": tipo,
        "contenido": salida,
        "problemas": problemas,
        "revisor_ok": revisor_ok,
        "historial": historial,
    }


def generar_con_revision(historia, avisar=lambda mensaje: None):
    """Ciclo completo para casos Gherkin."""
    return ciclo_de_revision(
        historia,
        generar_fn=generar,
        corregir_fn=corregir,
        revisar_fn=revisar,
        validar_fn=validar_texto,
        tipo="feature",
        avisar=avisar,
        que="escenarios",
    )
