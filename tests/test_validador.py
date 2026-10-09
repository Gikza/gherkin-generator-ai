"""Tests unitarios del validador: cada regla con casos que pasan y casos que fallan."""
from pathlib import Path

import pytest

from simulador import FEATURE_SIMULADO
from validador import regla_r04, regla_r07, regla_r08, regla_r20, validar_texto

RAIZ = Path(__file__).resolve().parent.parent
EJEMPLOS = RAIZ / "ejemplos"
ROTO = RAIZ / "pruebas_validador" / "roto.feature"


def leer(ruta):
    return Path(ruta).read_text(encoding="utf-8")


def reglas_con_fallas(texto):
    return {regla for regla, errores in validar_texto(texto).items() if errores}


# --- Archivos de referencia -------------------------------------------------

@pytest.mark.parametrize(
    "archivo",
    [
        "hu01_reserva_turno.feature",
        "hu02_registro_paciente.feature",
        "hu04_busqueda_productos.feature",
        "hu05_roles_reclamos.feature",
    ],
)
def test_ejemplos_validos_pasan_todas_las_reglas(archivo):
    assert reglas_con_fallas(leer(EJEMPLOS / archivo)) == set()


def test_hu03_falla_solo_r07_por_etiqueta_no_permitida():
    texto = leer(EJEMPLOS / "hu03_transferencia.feature")
    assert reglas_con_fallas(texto) == {"R07"}
    assert regla_r07(texto) == ["Etiqueta no permitida: @positivo"]


def test_archivo_roto_falla_las_cuatro_reglas_de_forma():
    assert reglas_con_fallas(leer(ROTO)) >= {"R04", "R05", "R07", "R08"}


def test_feature_del_simulador_es_valido():
    # Si el simulador devolviera un .feature inválido, los tests E2E serían engañosos.
    assert reglas_con_fallas(FEATURE_SIMULADO) == set()


# --- R04: idioma -------------------------------------------------------------

def test_r04_falla_sin_linea_de_idioma():
    assert regla_r04("Característica: X\n") == ['La primera línea no es "# language: es"']


def test_r04_detecta_palabras_clave_en_ingles():
    errores = regla_r04("# language: es\nCaracterística: X\n  Scenario: a\n")
    assert len(errores) == 1
    assert "Scenario: a" in errores[0]


# --- R08: etiquetas obligatorias --------------------------------------------

def test_r08_falla_si_falta_smoke():
    assert regla_r08("@negativo\nEscenario: a\n") == ["Falta al menos un escenario @smoke"]


def test_r08_pasa_con_smoke_y_negativo():
    assert regla_r08("@smoke\nEscenario: a\n@negativo\nEscenario: b\n") == []


# --- R20: cobertura ----------------------------------------------------------

FEATURE_CON_COBERTURA = """# language: es
Característica: X
  Escenario: Primero
    Dado algo
  Esquema del escenario: Segundo
    Dado <x>
    Ejemplos:
      | x |
      | 1 |
"""


def test_r20_pasa_si_la_cobertura_cita_escenarios_reales():
    texto = FEATURE_CON_COBERTURA + "# Cobertura: C1 -> Primero; Segundo (límites 1 y 2)\n"
    assert regla_r20(texto) == []


def test_r20_detecta_escenario_inexistente():
    texto = FEATURE_CON_COBERTURA + "# Cobertura: C1 -> Primero; Tercero inventado\n"
    assert regla_r20(texto) == [
        'La cobertura menciona un escenario que no existe: "Tercero inventado"'
    ]


def test_r20_ignora_criterios_que_no_aplican():
    texto = FEATURE_CON_COBERTURA + "# Cobertura: Rendimiento -> No hay criterios de rendimiento\n"
    assert regla_r20(texto) == []
