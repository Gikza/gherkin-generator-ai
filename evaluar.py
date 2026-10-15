"""Evaluación de la herramienta con la IA real: mide calidad, intentos, tiempo y tokens.

Corre un set fijo de casos (evaluacion/casos.json) una o varias veces y guarda:
  - evaluacion/resultados/<fecha>.json  (detalle de cada ejecución)
  - evaluacion/resultados/<fecha>.md    (resumen para leer o mostrar)

Uso:
  python evaluar.py                      (todos los casos, 1 vez)
  python evaluar.py --repeticiones 3     (cada caso 3 veces, para medir variabilidad)
  python evaluar.py --casos G01,R01      (solo algunos casos)

Cuesta créditos de la API: cada ejecución hace varias llamadas.
Con MODO_PRUEBA=1 usa el simulador (gratis), útil para probar el script.
"""
import argparse
import json
import os
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

import uso
from reporte import armar_entrada
from reporte_validador import validar_reporte
from validador import validar_texto

RAIZ = Path(__file__).resolve().parent
CASOS = RAIZ / "evaluacion" / "casos.json"
RESULTADOS = RAIZ / "evaluacion" / "resultados"


def funciones_de_generacion():
    """Devuelve las funciones reales o las del simulador, según MODO_PRUEBA."""
    if os.environ.get("MODO_PRUEBA") == "1":
        from simulador import generar_con_revision, generar_reporte_con_revision
    else:
        from generador import generar_con_revision
        from reporte import generar_reporte_con_revision
    return {"gherkin": generar_con_revision, "reporte": generar_reporte_con_revision}


def entrada_del_caso(caso):
    """Texto que se le da a la herramienta, igual que en la app."""
    if caso["tipo"] == "reporte":
        return armar_entrada(caso["descripcion"], caso.get("log", ""))
    return caso["entrada"]


def tipo_obtenido(resultado):
    """'preguntas', 'feature' o 'reporte'."""
    return resultado["tipo"]


def evaluar_resultado(caso, entrada, resultado):
    """Compara un resultado con lo que espera el caso. No llama a la IA.

    Devuelve un diccionario con las métricas y la lista de fallas (vacía = aprobado).
    """
    obtenido = tipo_obtenido(resultado)
    fallas = []
    if obtenido != caso["esperado"]:
        fallas.append(f"Se esperaba '{caso['esperado']}' y se obtuvo '{obtenido}'")

    metricas = {"tipo_obtenido": obtenido, "intentos": 0, "reglas_intento_1": [],
                "graves_intento_1": 0, "graves_finales": 0, "validacion_final": [],
                "b08_detectado": False}

    if obtenido == "preguntas":
        return metricas, fallas

    contenido = resultado["contenido"]
    historial = resultado.get("historial", [])
    primeros = historial[0]["problemas"] if historial else []
    metricas["intentos"] = len(historial)
    metricas["reglas_intento_1"] = sorted({p["regla"] for p in primeros})
    metricas["graves_intento_1"] = sum(1 for p in primeros if p.get("gravedad") == "alta")
    metricas["graves_finales"] = sum(1 for p in resultado.get("problemas", [])
                                     if p.get("gravedad") == "alta")
    metricas["b08_detectado"] = any(p["regla"] == "B08"
                                    for paso in historial for p in paso["problemas"])

    if obtenido == "reporte":
        validaciones = validar_reporte(contenido, entrada)
    else:
        validaciones = validar_texto(contenido)
    # Igual que en el ciclo: si una regla no se pudo evaluar, no es culpa del resultado.
    metricas["validacion_final"] = sorted(
        r for r, errores in validaciones.items()
        if any(not e.startswith("No se pudo evaluar") for e in errores)
    )

    if metricas["graves_finales"]:
        fallas.append(f"Quedaron {metricas['graves_finales']} problema(s) grave(s) sin resolver")
    if metricas["validacion_final"]:
        fallas.append("Validación automática con fallas: " + ", ".join(metricas["validacion_final"]))

    texto = contenido.lower()
    for prohibido in caso.get("no_debe_contener", []):
        if prohibido.lower() in texto:
            fallas.append(f'Contiene "{prohibido}", que la entrada no menciona')
    for obligatorio in caso.get("debe_contener", []):
        if obligatorio.lower() not in texto:
            fallas.append(f'No contiene "{obligatorio}"')

    return metricas, fallas


def ejecutar_caso(caso, generar, repeticion):
    """Corre un caso una vez y devuelve el registro de la ejecución."""
    entrada = entrada_del_caso(caso)
    uso.reiniciar()
    inicio = time.monotonic()
    registro = {"caso": caso["id"], "nombre": caso["nombre"], "tipo": caso["tipo"],
                "repeticion": repeticion}
    try:
        resultado = generar(entrada)
        metricas, fallas = evaluar_resultado(caso, entrada, resultado)
        registro.update(metricas)
        registro["contenido"] = resultado["contenido"]
    except Exception as error:  # un error de la API no corta la evaluación entera
        fallas = [f"Error al generar: {type(error).__name__}: {error}"]
        registro["tipo_obtenido"] = "error"
    registro["fallas"] = fallas
    registro["aprobado"] = not fallas
    registro["segundos"] = round(time.monotonic() - inicio, 1)
    registro.update(uso.leer())
    return registro


def resumir(ejecuciones):
    """Métricas globales a partir de la lista de ejecuciones."""
    total = len(ejecuciones)
    generadas = [e for e in ejecuciones if e.get("tipo_obtenido") in ("feature", "reporte")]
    reglas = Counter(r for e in generadas for r in e.get("reglas_intento_1", []))
    return {
        "ejecuciones": total,
        "aprobadas": sum(e["aprobado"] for e in ejecuciones),
        "porcentaje_aprobadas": round(100 * sum(e["aprobado"] for e in ejecuciones) / total) if total else 0,
        "generadas": len(generadas),
        "con_graves_en_intento_1": sum(1 for e in generadas if e.get("graves_intento_1")),
        "con_graves_finales": sum(1 for e in generadas if e.get("graves_finales")),
        "con_b08_detectado": sum(1 for e in generadas if e.get("b08_detectado")),
        "intentos_promedio": round(sum(e["intentos"] for e in generadas) / len(generadas), 1) if generadas else 0,
        "segundos_promedio": round(sum(e["segundos"] for e in ejecuciones) / total, 1) if total else 0,
        "llamadas_total": sum(e["llamadas"] for e in ejecuciones),
        "tokens_entrada_total": sum(e["tokens_entrada"] for e in ejecuciones),
        "tokens_salida_total": sum(e["tokens_salida"] for e in ejecuciones),
        "reglas_mas_frecuentes_intento_1": reglas.most_common(5),
    }


def a_markdown(resumen, ejecuciones, modelo):
    """Resumen legible de la evaluación."""
    r = resumen
    lineas = [
        f"# Evaluación — {datetime.now():%Y-%m-%d %H:%M}",
        "",
        f"Modelo: `{modelo}` · Ejecuciones: {r['ejecuciones']}",
        "",
        "## Resumen",
        "",
        "| Métrica | Valor |",
        "|---|---|",
        f"| Aprobadas | {r['aprobadas']} de {r['ejecuciones']} ({r['porcentaje_aprobadas']} %) |",
        f"| Con problemas graves en el intento 1 | {r['con_graves_en_intento_1']} de {r['generadas']} |",
        f"| Con problemas graves al final | {r['con_graves_finales']} de {r['generadas']} |",
        f"| Datos inventados detectados por código (B08) | {r['con_b08_detectado']} de {r['generadas']} |",
        f"| Intentos promedio | {r['intentos_promedio']} |",
        f"| Tiempo promedio | {r['segundos_promedio']} s |",
        f"| Llamadas a la API | {r['llamadas_total']} |",
        f"| Tokens (entrada / salida) | {r['tokens_entrada_total']} / {r['tokens_salida_total']} |",
        "",
        "Reglas más frecuentes en el intento 1: "
        + (", ".join(f"{regla} ({n})" for regla, n in r["reglas_mas_frecuentes_intento_1"]) or "ninguna"),
        "",
        "## Detalle",
        "",
        "| Caso | Resultado | Intentos | Reglas en el intento 1 | Tiempo | Fallas |",
        "|---|---|---|---|---|---|",
    ]
    for e in ejecuciones:
        estado = "✅" if e["aprobado"] else "❌"
        lineas.append(
            f"| {e['caso']} {e['nombre']} | {estado} {e.get('tipo_obtenido', '')} | {e.get('intentos', 0)} "
            f"| {', '.join(e.get('reglas_intento_1', [])) or '-'} | {e['segundos']} s "
            f"| {'; '.join(e['fallas']) or '-'} |"
        )
    return "\n".join(lineas) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Evalúa la herramienta con un set fijo de casos.")
    parser.add_argument("--repeticiones", type=int, default=1)
    parser.add_argument("--casos", default="", help="IDs separados por coma, por ejemplo G01,R01")
    args = parser.parse_args()

    casos = json.loads(CASOS.read_text(encoding="utf-8"))["casos"]
    if args.casos:
        elegidos = {c.strip() for c in args.casos.split(",")}
        casos = [c for c in casos if c["id"] in elegidos]

    generar = funciones_de_generacion()
    modelo = "simulador" if os.environ.get("MODO_PRUEBA") == "1" else os.environ.get("CLAUDE_MODEL", "?")
    total = len(casos) * args.repeticiones
    print(f"Evaluando {len(casos)} caso(s) x {args.repeticiones} = {total} ejecución(es) con {modelo}\n")

    ejecuciones = []
    for repeticion in range(1, args.repeticiones + 1):
        for caso in casos:
            print(f"[{len(ejecuciones) + 1}/{total}] {caso['id']} {caso['nombre']}...", flush=True)
            registro = ejecutar_caso(caso, generar[caso["tipo"]], repeticion)
            ejecuciones.append(registro)
            estado = "OK" if registro["aprobado"] else "FALLA: " + "; ".join(registro["fallas"])
            print(f"      {estado} ({registro['segundos']} s)")

    resumen = resumir(ejecuciones)
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    nombre = f"{datetime.now():%Y-%m-%d_%H%M}"
    if modelo == "simulador":
        nombre += "_simulador"
    (RESULTADOS / f"{nombre}.json").write_text(
        json.dumps({"modelo": modelo, "resumen": resumen, "ejecuciones": ejecuciones},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    (RESULTADOS / f"{nombre}.md").write_text(a_markdown(resumen, ejecuciones, modelo), encoding="utf-8")

    print(f"\nAprobadas: {resumen['aprobadas']} de {resumen['ejecuciones']} ({resumen['porcentaje_aprobadas']} %)")
    print(f"Tokens: {resumen['tokens_entrada_total']} de entrada / {resumen['tokens_salida_total']} de salida")
    print(f"Resultados en evaluacion/resultados/{nombre}.md")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    main()
