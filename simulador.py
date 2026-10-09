"""Simulador de la IA para los tests de interfaz (modo prueba).

Se activa con la variable de entorno MODO_PRUEBA=1. Devuelve siempre la misma
respuesta según palabras clave de la historia, para que los tests sean
predecibles, gratis y puedan provocar errores a propósito.

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

    if "rápida" in historia.lower():
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
