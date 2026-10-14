"""Simulador de la IA para los tests de interfaz (modo prueba).

Se activa con la variable de entorno MODO_PRUEBA=1. Devuelve siempre la misma
respuesta según palabras clave de la historia, para que los tests sean
predecibles, gratis y puedan provocar errores a propósito.

  - Historia con "Aclaraciones:"  -> un .feature válido (ya se respondieron las preguntas)
  - Historia con "rápida"        -> preguntas de aclaración
  - Historia con "ERROR_TIMEOUT" -> la IA tarda demasiado
  - Cualquier otra historia      -> un .feature válido
"""
FEATURE_SIMULADO = """# language: es
# Supuesto: el usuario está registrado.
@regresion
Característica: Inicio de sesión

  @smoke
  Escenario: Inicio de sesión exitoso
    Dado que el usuario está registrado
    Cuando inicia sesión con credenciales válidas
    Entonces accede a su cuenta

  @negativo
  Escenario: Inicio de sesión con contraseña incorrecta
    Dado que el usuario está registrado
    Cuando inicia sesión con una contraseña incorrecta
    Entonces se le informa que las credenciales no son válidas

# Cobertura: Iniciar sesión -> Inicio de sesión exitoso; Inicio de sesión con contraseña incorrecta
"""


def generar_con_revision(historia, avisar=lambda mensaje: None):
    """Misma firma que generador.generar_con_revision, pero sin llamar a la API."""
    avisar("Modo prueba: respuesta simulada")

    if "ERROR_TIMEOUT" in historia:
        raise TimeoutError("Simulación: la IA tardó demasiado")

    # Si ya trae respuestas, no vuelve a preguntar: pasa directo a generar.
    if "rápida" in historia.lower() and "Aclaraciones:" not in historia:
        return {
            "tipo": "preguntas",
            "contenido": "1. ¿Cuál es el tiempo máximo de respuesta?\n2. ¿Por qué campos se busca?",
        }

    return {
        "tipo": "feature",
        "contenido": FEATURE_SIMULADO,
        "problemas": [],
        "revisor_ok": True,
        "historial": [{"intento": 1, "problemas": []}],
    }


# --- Reportes de bugs ------------------------------------------------------
#   - Descripción con "no anda"        -> preguntas de aclaración
#   - Descripción con "ERROR_TIMEOUT"  -> la IA tarda demasiado
#   - Cualquier otra descripción       -> un reporte válido

REPORTE_SIMULADO = """**Título:** [Login] Iniciar sesión con credenciales válidas – muestra error 500
**Entorno:** [Completar: ambiente, navegador y versión, sistema operativo]
**Precondiciones:** El usuario de prueba está registrado.
**Pasos para reproducir:**
1. Ingresar a la pantalla de inicio de sesión.
2. Completar usuario y contraseña válidos.
3. Confirmar el inicio de sesión.
**Resultado esperado:** El usuario accede a su cuenta.
**Resultado actual:** Se muestra el mensaje "Error 500: Internal Server Error" y el usuario no accede.
**Severidad:** Crítica – bloquea el inicio de sesión y no hay alternativa.
**Frecuencia:** Siempre
**Evidencia:** [Completar: captura del error]
**Casos de regresión:**
Escenario: Inicio de sesión exitoso con credenciales válidas
  Dado que el usuario está registrado
  Cuando inicia sesión con credenciales válidas
  Entonces accede a su cuenta
"""


def generar_reporte_con_revision(entrada, avisar=lambda mensaje: None):
    """Misma firma que reporte.generar_reporte_con_revision, pero sin llamar a la API."""
    avisar("Modo prueba: respuesta simulada")

    if "ERROR_TIMEOUT" in entrada:
        raise TimeoutError("Simulación: la IA tardó demasiado")

    if "no anda" in entrada.lower() and "Aclaraciones:" not in entrada:
        return {
            "tipo": "preguntas",
            "contenido": "1. ¿Qué pasa exactamente cuando falla?\n2. ¿Qué debería pasar?",
        }

    return {
        "tipo": "reporte",
        "contenido": REPORTE_SIMULADO,
        "problemas": [],
        "revisor_ok": True,
        "historial": [{"intento": 1, "problemas": []}],
    }
