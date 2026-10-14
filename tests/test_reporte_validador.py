"""Tests unitarios del validador de reportes de bugs (B01 a B07)."""
import pytest

from reporte import armar_entrada
from reporte_validador import leer_campos, validar_reporte
from simulador import REPORTE_SIMULADO


def reglas_con_fallas(texto):
    return {regla for regla, errores in validar_reporte(texto).items() if errores}


def cambiar(campo, nuevo):
    """Devuelve el reporte simulado con un campo reemplazado (o quitado si nuevo es None)."""
    lineas = []
    saltear = False
    for linea in REPORTE_SIMULADO.splitlines():
        if linea.startswith("**"):
            saltear = linea.startswith(f"**{campo}:**")
            if saltear and nuevo is not None:
                lineas.append(f"**{campo}:** {nuevo}")
                continue
        if not saltear:
            lineas.append(linea)
    return "\n".join(lineas) + "\n"


def test_el_reporte_del_simulador_pasa_todas_las_reglas():
    assert reglas_con_fallas(REPORTE_SIMULADO) == set()


def test_lee_campos_de_varias_lineas():
    campos = dict(leer_campos(REPORTE_SIMULADO))
    assert campos["Pasos para reproducir"].startswith("1. Ingresar")
    assert "Entonces accede a su cuenta" in campos["Casos de regresión"]


def test_b01_falta_un_campo_obligatorio():
    assert "B01" in reglas_con_fallas(cambiar("Entorno", None))


def test_b01_campos_fuera_de_orden():
    texto = REPORTE_SIMULADO.replace("**Severidad:**", "**TEMP:**").replace(
        "**Frecuencia:** Siempre", "**Severidad:** Crítica – bloquea el login.").replace(
        "**TEMP:** Crítica – bloquea el inicio de sesión y no hay alternativa.", "**Frecuencia:** Siempre")
    assert "B01" in reglas_con_fallas(texto)


@pytest.mark.parametrize("titulo", [
    "Login falla con error 500",               # sin [Módulo]
    "[Login] " + "x" * 80,                     # más de 80 caracteres
])
def test_b02_titulo_invalido(titulo):
    assert "B02" in reglas_con_fallas(cambiar("Título", titulo))


@pytest.mark.parametrize("severidad", ["Urgente – no deja entrar", "Alta", "Alta – "])
def test_b03_severidad_invalida_o_sin_justificacion(severidad):
    assert "B03" in reglas_con_fallas(cambiar("Severidad", severidad))


@pytest.mark.parametrize("frecuencia", ["Siempre", "Una vez", "Intermitente (2 de 5 intentos)",
                                        "[Completar: frecuencia]"])
def test_b04_frecuencias_permitidas(frecuencia):
    assert "B04" not in reglas_con_fallas(cambiar("Frecuencia", frecuencia))


@pytest.mark.parametrize("frecuencia", ["A veces", "Intermitente"])
def test_b04_frecuencias_no_permitidas(frecuencia):
    assert "B04" in reglas_con_fallas(cambiar("Frecuencia", frecuencia))


def test_b05_un_solo_paso():
    texto = REPORTE_SIMULADO.replace("2. Completar usuario y contraseña válidos.\n", "").replace(
        "3. Confirmar el inicio de sesión.\n", "")
    assert "B05" in reglas_con_fallas(texto)


def test_b06_resultado_actual_sin_completar():
    assert "B06" in reglas_con_fallas(cambiar("Resultado actual", "[Completar: qué pasa]"))


def test_b06_esperado_igual_al_actual():
    assert "B06" in reglas_con_fallas(cambiar("Resultado actual", "El usuario accede a su cuenta."))


def test_b07_sin_casos_de_regresion():
    texto = REPORTE_SIMULADO.split("**Casos de regresión:**")[0] + "**Casos de regresión:**\n"
    assert "B07" in reglas_con_fallas(texto)


def test_b07_mas_de_dos_casos():
    caso = "Escenario: Otro caso\n  Dado algo\n  Cuando pasa algo\n  Entonces se ve algo\n"
    assert "B07" in reglas_con_fallas(REPORTE_SIMULADO + caso + caso)


def test_armar_entrada_con_y_sin_log():
    assert armar_entrada("  El login falla  ") == "Descripción del QA:\nEl login falla"
    con_log = armar_entrada("El login falla", "Error 500")
    assert con_log.endswith("Log o error de consola:\nError 500")
