"""Tests unitarios del validador de reportes de bugs (B01 a B07)."""
import pytest

from reporte import armar_entrada
from reporte_validador import leer_campos, validar_reporte
from simulador import ENTRADA_SIMULADA, REPORTE_SIMULADO


def reglas_con_fallas(texto, entrada=ENTRADA_SIMULADA):
    return {regla for regla, errores in validar_reporte(texto, entrada).items() if errores}


def cambiar(campo, nuevo, texto=REPORTE_SIMULADO):
    """Devuelve el reporte con un campo reemplazado (o quitado si nuevo es None)."""
    lineas = []
    saltear = False
    for linea in texto.splitlines():
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


# --- B08: datos inventados, verificados con código ----------------------------

LOG = ("POST /api/carrito/cupon 500 - TypeError: Cannot read properties of undefined "
       "(reading 'descuento')")
ENTRADA_CUPON = armar_entrada(
    "Al aplicar el cupón VERANO10 en el carrito, el total no cambia y aparece un mensaje en rojo.",
    LOG,
)


# Reporte simulado adaptado al bug del cupón: sin cambios, B08 no encuentra nada inventado.
REPORTE_CUPON = cambiar("Título", "[Carrito] Aplicar cupón VERANO10 – el total no cambia",
                        cambiar("Resultado actual", f"El total no cambia. Log: {LOG}"))


def con_entrada_del_cupon(campo_cambiado, valor):
    return reglas_con_fallas(cambiar(campo_cambiado, valor, REPORTE_CUPON), ENTRADA_CUPON)


def test_b08_el_reporte_del_cupon_no_tiene_datos_inventados():
    assert "B08" not in reglas_con_fallas(REPORTE_CUPON, ENTRADA_CUPON)


def test_b08_acepta_datos_copiados_del_log():
    assert "B08" not in con_entrada_del_cupon("Resultado actual", f"El total no cambia. Log: {LOG}")


def test_b08_ignora_lo_que_esta_en_completar():
    assert "B08" not in con_entrada_del_cupon("Entorno", "[Completar: navegador (Chrome, Firefox) y versión]")


@pytest.mark.parametrize("campo_cambiado, inventado", [
    ("Entorno", "Chrome 118 en Windows 11"),                       # plataforma y versión
    ("Resultado actual", 'Aparece "Cupón inválido"'),               # mensaje entre comillas
    ("Evidencia", "Ver https://jira.ejemplo.com/BUG-1"),            # URL
    ("Pasos para reproducir", "1. Abrir /checkout/pago\n2. Aplicar el cupón."),  # ruta
])
def test_b08_detecta_datos_inventados(campo_cambiado, inventado):
    assert "B08" in con_entrada_del_cupon(campo_cambiado, inventado)


def test_b08_detecta_adjuntos_dados_por_hechos():
    # El caso real que encontró el revisor IA, ahora detectado con código.
    evidencia = ("Captura de pantalla del carrito con el mensaje en rojo, captura de la pestaña "
                 "Network y el log completo de consola.")
    assert "B08" in con_entrada_del_cupon("Evidencia", evidencia)


def test_b08_acepta_adjuntos_pedidos_con_completar():
    evidencia = f"Log: {LOG}. [Completar: adjuntar captura del mensaje en rojo]"
    assert "B08" not in con_entrada_del_cupon("Evidencia", evidencia)


def test_b08_no_revisa_hipotesis_ni_resultado_esperado():
    texto = cambiar("Resultado esperado", "La llamada responde 200.")
    texto = texto.replace("**Casos de regresión:**", "**Notas:** Posible `null` en el cupón.\n**Casos de regresión:**")
    assert "B08" not in reglas_con_fallas(texto)
