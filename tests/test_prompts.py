"""Tests de los prompts: generador y revisor tienen que compartir los mismos criterios."""
import json

from prompt import CRITERIO_LONGITUD, CRITERIO_PERMISOS, CRITERIO_SUPUESTOS, SYSTEM_PROMPT
from reporte_prompt import GRAVEDAD_REPORTE
from revisor import REVISOR_PROMPT


def test_generador_y_revisor_usan_el_mismo_criterio_de_permisos():
    # Si cada uno tuviera su propio criterio, el revisor marcaría como R23
    # los casos de permisos que el generador agrega (hallazgo del 14/10/2026).
    assert CRITERIO_PERMISOS in SYSTEM_PROMPT
    assert CRITERIO_PERMISOS in REVISOR_PROMPT


def test_el_ejemplo_de_json_del_revisor_es_valido():
    # El prompt del revisor es un f-string: las llaves del JSON tienen que quedar simples.
    ejemplo = REVISOR_PROMPT.strip().splitlines()[-1]
    assert json.loads(ejemplo)["problemas"][0]["regla"] == "R11"


def test_la_severidad_del_reporte_es_solo_una_sugerencia():
    # Decisión de diseño: la IA no corrige la severidad por su cuenta; la decide la QA.
    assert GRAVEDAD_REPORTE["B11"] == "baja"


def test_generador_y_revisor_usan_el_mismo_criterio_de_longitud():
    # Evaluación 2026-10-15_1821 (G05): el generador inventaba una longitud máxima
    # y el revisor la marcaba como requisito inventado (R23).
    assert CRITERIO_LONGITUD in SYSTEM_PROMPT
    assert CRITERIO_LONGITUD in REVISOR_PROMPT


def test_generador_y_revisor_usan_el_mismo_criterio_de_supuestos():
    # Evaluación 2026-10-15_1901 (G05): un supuesto agregaba comportamiento nuevo
    # ("el enlace es de un solo uso") y el revisor lo marcaba como inventado (R23).
    assert CRITERIO_SUPUESTOS in SYSTEM_PROMPT
    assert CRITERIO_SUPUESTOS in REVISOR_PROMPT
