"""Tests de la evaluación: cómo se califica un resultado y cómo se resume, sin llamar a la IA."""
import json

from evaluar import CASOS, a_markdown, entrada_del_caso, evaluar_resultado, resumir
from simulador import ENTRADA_SIMULADA, REPORTE_SIMULADO

CASO_REPORTE = {"id": "X1", "nombre": "Prueba", "tipo": "reporte", "esperado": "reporte",
                "descripcion": "", "no_debe_contener": ["Chrome"], "debe_contener": ["Error 500"]}


def resultado(contenido=REPORTE_SIMULADO, historial=None, problemas=None, tipo="reporte"):
    return {"tipo": tipo, "contenido": contenido,
            "historial": historial if historial is not None else [{"intento": 1, "problemas": []}],
            "problemas": problemas or []}


def test_los_casos_del_set_estan_bien_formados():
    casos = json.loads(CASOS.read_text(encoding="utf-8"))["casos"]
    ids = [c["id"] for c in casos]
    assert len(ids) == len(set(ids)), "IDs repetidos"
    for caso in casos:
        assert caso["tipo"] in ("gherkin", "reporte")
        assert caso["esperado"] in ("feature", "reporte", "preguntas")
        assert entrada_del_caso(caso).strip()


def test_aprueba_un_reporte_correcto():
    metricas, fallas = evaluar_resultado(CASO_REPORTE, ENTRADA_SIMULADA, resultado())
    assert fallas == []
    assert metricas["intentos"] == 1


def test_falla_si_el_tipo_no_es_el_esperado():
    _, fallas = evaluar_resultado(CASO_REPORTE, ENTRADA_SIMULADA,
                                  {"tipo": "preguntas", "contenido": "1. ¿Qué pasa?"})
    assert any("Se esperaba" in f for f in fallas)


def test_falla_si_contiene_un_dato_prohibido():
    texto = REPORTE_SIMULADO.replace("[Completar: ambiente, navegador y versión, sistema operativo]", "Chrome")
    _, fallas = evaluar_resultado(CASO_REPORTE, ENTRADA_SIMULADA, resultado(texto))
    assert any('"Chrome"' in f for f in fallas)


def test_falla_si_falta_un_texto_obligatorio():
    caso = dict(CASO_REPORTE, debe_contener=["timeout"])
    _, fallas = evaluar_resultado(caso, ENTRADA_SIMULADA, resultado())
    assert any('"timeout"' in f for f in fallas)


def test_cuenta_graves_del_intento_1_y_detecta_b08():
    historial = [
        {"intento": 1, "problemas": [{"regla": "B08", "gravedad": "alta", "detalle": "x"},
                                     {"regla": "B15", "gravedad": "baja", "detalle": "y"}]},
        {"intento": 2, "problemas": []},
    ]
    metricas, fallas = evaluar_resultado(CASO_REPORTE, ENTRADA_SIMULADA, resultado(historial=historial))
    assert metricas["graves_intento_1"] == 1
    assert metricas["reglas_intento_1"] == ["B08", "B15"]
    assert metricas["b08_detectado"] is True
    assert fallas == []  # se corrigió en el intento 2


def test_falla_si_quedan_graves_al_final():
    problemas = [{"regla": "B12", "gravedad": "alta", "detalle": "x"}]
    _, fallas = evaluar_resultado(CASO_REPORTE, ENTRADA_SIMULADA, resultado(problemas=problemas))
    assert any("grave" in f for f in fallas)


def test_resumen_y_markdown():
    ejecuciones = [
        {"caso": "A", "nombre": "a", "aprobado": True, "tipo_obtenido": "reporte", "intentos": 2,
         "reglas_intento_1": ["B12"], "graves_intento_1": 1, "graves_finales": 0, "b08_detectado": False,
         "segundos": 10.0, "llamadas": 4, "tokens_entrada": 100, "tokens_salida": 50, "fallas": []},
        {"caso": "B", "nombre": "b", "aprobado": False, "tipo_obtenido": "preguntas", "intentos": 0,
         "segundos": 2.0, "llamadas": 1, "tokens_entrada": 10, "tokens_salida": 5,
         "fallas": ["Se esperaba 'reporte' y se obtuvo 'preguntas'"]},
    ]
    r = resumir(ejecuciones)
    assert r["aprobadas"] == 1 and r["porcentaje_aprobadas"] == 50
    assert r["generadas"] == 1 and r["con_graves_en_intento_1"] == 1
    assert r["tokens_entrada_total"] == 110
    assert r["reglas_mas_frecuentes_intento_1"] == [("B12", 1)]
    md = a_markdown(r, ejecuciones, "modelo-x")
    assert "1 de 2 (50 %)" in md and "| B b |" in md
