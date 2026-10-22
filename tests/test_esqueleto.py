"""Tests del esqueleto Playwright: conversión de pasos a Cucumber Expressions y el .zip."""
import io
import json
import zipfile
from pathlib import Path

import pytest

from esqueleto import (a_expresion, coincide, definiciones, empaquetar, generar_esqueleto,
                       generar_pasos_ts, problemas_de_coincidencia)
from simulador import FEATURE_SIMULADO

RAIZ = Path(__file__).resolve().parent.parent
FEATURES = sorted((RAIZ / "ejemplos").glob("*.feature"))


@pytest.mark.parametrize("texto, esperado", [
    ('ingresa el email "ana@ejemplo.com"', ('ingresa el email {string}', ["string"])),
    ("agrega 3 productos", ("agrega {int} productos", ["int"])),
    ("aplica un descuento de -5%", ("aplica un descuento de {int}%", ["int"])),
    ("pesa 2.5 kg", ("pesa {float} kg", ["float"])),
    ("transfiere $1.000,00", ("transfiere $1.000,00", [])),   # formato local: literal
    ("el subtotal es $20.000", ("el subtotal es $20.000", [])),  # punto de miles, no decimal
    ("el turno del 2026-10-22", ("el turno del 2026-10-22", [])),  # fecha: literal
    ("ve el total (con IVA) en ARS/USD", (r"ve el total \(con IVA\) en ARS\/USD", [])),
])
def test_a_expresion(texto, esperado):
    assert a_expresion(texto) == esperado


def test_la_expresion_coincide_con_su_texto():
    for texto in ['ingresa "x" y "y"', "agrega 3 productos", "ve el total (con IVA) en ARS/USD"]:
        assert coincide(a_expresion(texto)[0], texto)


FEATURE = """# language: es
Característica: Carrito

  Antecedentes:
    Dado que el usuario "ana" inició sesión

  Escenario: Agregar
    Cuando agrega 2 productos
    Y agrega 3 productos
    Entonces ve 5 productos en el carrito
    Pero no ve el aviso de stock

  Esquema del escenario: Cupones
    Cuando aplica el cupón "<codigo>"
    Entonces el cupón queda <estado>

    Ejemplos:
      | codigo | estado    |
      | A10    | aplicado  |
      | VIEJO  | rechazado |
"""


def test_definiciones_sin_repetir_y_con_palabra_heredada():
    defs = {d["expresion"]: d for d in definiciones(FEATURE)}
    assert defs["agrega {int} productos"]["funcion"] == "When"
    assert defs["no ve el aviso de stock"]["funcion"] == "Then"  # "Pero" hereda Entonces
    assert defs["que el usuario {string} inició sesión"]["escenarios"] == ["Antecedentes"]
    assert len([e for e in defs if e.startswith("agrega")]) == 1


def test_esquema_se_expande_por_fila():
    expresiones = [d["expresion"] for d in definiciones(FEATURE)]
    assert "aplica el cupón {string}" in expresiones
    assert "el cupón queda aplicado" in expresiones
    assert "el cupón queda rechazado" in expresiones


def test_int_y_float_en_el_mismo_lugar_quedan_en_una():
    feature = FEATURE.replace("Y agrega 3 productos", "Y agrega 2.5 productos")
    expresiones = [d["expresion"] for d in definiciones(feature)]
    assert "agrega {float} productos" in expresiones
    assert "agrega {int} productos" not in expresiones


@pytest.mark.parametrize("ruta", FEATURES, ids=lambda r: r.name)
def test_ejemplos_sin_pasos_ambiguos_ni_faltantes(ruta):
    assert problemas_de_coincidencia(ruta.read_text(encoding="utf-8")) == []


def test_feature_simulado_sin_problemas():
    assert problemas_de_coincidencia(FEATURE_SIMULADO) == []


def test_pasos_ts_pendientes_y_tipados():
    ts = generar_pasos_ts(FEATURE)
    assert "import { createBdd } from 'playwright-bdd';" in ts
    assert "When('agrega {int} productos', async ({ page }, numero1: number) => {" in ts
    assert ts.count("throw new Error(") == len(definiciones(FEATURE))
    assert "getByRole(" not in ts.replace("page.getByRole(...)", "")  # sin selectores inventados


def test_zip_con_el_proyecto_completo():
    archivos = generar_esqueleto(FEATURE, nombre="carrito")
    contenido = zipfile.ZipFile(io.BytesIO(empaquetar(archivos)))
    nombres = set(contenido.namelist())
    assert nombres == {f"esqueleto-playwright/{r}" for r in [
        "features/carrito.feature", "steps/pasos.ts", "playwright.config.ts",
        "package.json", "README.md", ".gitignore"]}
    package = json.loads(contenido.read("esqueleto-playwright/package.json"))
    assert "playwright-bdd" in package["devDependencies"]
    assert contenido.read("esqueleto-playwright/features/carrito.feature").decode() == FEATURE
