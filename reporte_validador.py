"""Validador de reportes de bugs: reglas que se pueden verificar sin IA.

  B01 - Están todos los campos obligatorios, sin repetir y en orden
  B02 - Título con [Módulo] al principio y de 80 caracteres como máximo
  B03 - Severidad Crítica, Alta, Media o Baja, con justificación
  B04 - Frecuencia Siempre, Intermitente (x de y intentos), Una vez o [Completar: ...]
  B05 - Al menos 2 pasos numerados
  B06 - Resultado esperado y actual completos y distintos
  B07 - 1 o 2 casos de regresión en Gherkin
  B08 - Los datos concretos del reporte (URLs, rutas, códigos, versiones, textos entre
        comillas, navegadores y sistemas) aparecen en lo que contó el QA: no están inventados
"""
import re

from reporte_prompt import MARCA_COMPLETAR

CAMPOS = [
    "Título", "Entorno", "Precondiciones", "Pasos para reproducir",
    "Resultado esperado", "Resultado actual", "Severidad", "Frecuencia",
    "Evidencia", "Notas", "Casos de regresión",
]
OPCIONALES = {"Notas"}
OBLIGATORIOS = [c for c in CAMPOS if c not in OPCIONALES]

_ENCABEZADO = re.compile(r"^\*\*(" + "|".join(map(re.escape, CAMPOS)) + r"):\*\*\s*(.*)$")


def leer_campos(texto):
    """Devuelve la lista de (campo, contenido) en el orden en que aparecen."""
    campos = []
    for linea in texto.splitlines():
        coincidencia = _ENCABEZADO.match(linea.strip())
        if coincidencia:
            campos.append([coincidencia.group(1), coincidencia.group(2)])
        elif campos:
            campos[-1][1] += "\n" + linea
    return [(campo, contenido.strip()) for campo, contenido in campos]


def campo(texto, nombre):
    """Contenido del primer campo con ese nombre, o "" si no está."""
    return next((c for n, c in leer_campos(texto) if n == nombre), "")


def regla_b01(texto):
    """Todos los campos obligatorios, sin repetir y en el orden del formato."""
    nombres = [n for n, _ in leer_campos(texto)]
    errores = [f"Falta el campo {c}" for c in OBLIGATORIOS if c not in nombres]
    errores += [f"Campo repetido: {c}" for c in CAMPOS if nombres.count(c) > 1]
    posiciones = [CAMPOS.index(n) for n in nombres]
    if posiciones != sorted(posiciones):
        errores.append("Los campos no están en el orden del formato")
    return errores


def regla_b02(texto):
    """Título con [Módulo] y de 80 caracteres como máximo."""
    titulo = campo(texto, "Título")
    if not titulo:
        return ["El título está vacío"]
    errores = []
    if not re.match(r"^\[[^\]]+\]\s*\S", titulo):
        errores.append("El título no empieza con [Módulo]")
    if len(titulo) > 80:
        errores.append(f"El título tiene {len(titulo)} caracteres (máximo 80)")
    return errores


def regla_b03(texto):
    """Severidad con un valor de la escala y una justificación."""
    severidad = campo(texto, "Severidad")
    coincidencia = re.match(r"^(Crítica|Alta|Media|Baja)\b\s*[-–—:,.]?\s*(.*)$", severidad)
    if not coincidencia:
        return [f'Severidad fuera de la escala: "{severidad}"']
    if not coincidencia.group(2).strip():
        return ["La severidad no tiene justificación"]
    return []


def regla_b04(texto):
    """Frecuencia con un valor permitido."""
    frecuencia = campo(texto, "Frecuencia").rstrip(".")
    permitida = (
        frecuencia in ("Siempre", "Una vez")
        or re.fullmatch(r"Intermitente \(\d+ de \d+ intentos?\)", frecuencia)
        or frecuencia.startswith(MARCA_COMPLETAR)
    )
    return [] if permitida else [f'Frecuencia no permitida: "{frecuencia}"']


def regla_b05(texto):
    """Al menos 2 pasos numerados."""
    pasos = [l for l in campo(texto, "Pasos para reproducir").splitlines()
             if re.match(r"^\s*\d+[.)]\s+\S", l)]
    return [] if len(pasos) >= 2 else [f"Hay {len(pasos)} paso(s) numerado(s); se necesitan al menos 2"]


def regla_b06(texto):
    """Resultado esperado y actual completos y distintos."""
    esperado = campo(texto, "Resultado esperado")
    actual = campo(texto, "Resultado actual")
    errores = []
    for nombre, valor in (("esperado", esperado), ("actual", actual)):
        if not valor or valor.startswith(MARCA_COMPLETAR):
            errores.append(f"Falta el resultado {nombre}")
    if not errores and esperado.lower() == actual.lower():
        errores.append("El resultado esperado y el actual son iguales")
    return errores


def regla_b07(texto):
    """1 o 2 casos de regresión en Gherkin, con al menos un Entonces."""
    casos = campo(texto, "Casos de regresión")
    lineas = [l.strip() for l in casos.splitlines()]
    escenarios = [l for l in lineas if l.startswith(("Escenario:", "Esquema del escenario:"))]
    errores = []
    if not 1 <= len(escenarios) <= 2:
        errores.append(f"Hay {len(escenarios)} caso(s) de regresión; tienen que ser 1 o 2")
    if escenarios and not any(l.startswith("Entonces ") for l in lineas):
        errores.append("Los casos de regresión no tienen un paso Entonces")
    return errores


# --- B08: datos inventados, verificados con código y no con la IA -----------------
# Campos donde un dato concreto tiene que venir sí o sí de lo que contó el QA.
# Quedan afuera el resultado esperado, las notas (hipótesis) y los casos de regresión,
# porque describen lo que debería pasar o lo que se sospecha, no lo que pasó.
CAMPOS_VERIFICABLES = [
    "Título", "Entorno", "Precondiciones", "Pasos para reproducir",
    "Resultado actual", "Frecuencia", "Evidencia",
]

NOMBRES_DE_PLATAFORMAS = [
    "Chrome", "Firefox", "Safari", "Edge", "Opera", "Brave",
    "Windows", "macOS", "Linux", "Ubuntu", "Android", "iOS", "iPhone", "iPad",
]

_DATOS_CONCRETOS = [
    r'"([^"\n]{3,})"',                     # "texto entre comillas"
    r"«([^»\n]{3,})»",                      # «texto entre comillas»
    r"`([^`\n]{3,})`",                      # `código`
    r"(https?://[^\s)\]]+)",               # URLs
    r"(?<![\w/])(/[\w.\-{}]+(?:/[\w.\-{}]+)*)",  # rutas como /api/carrito/cupon
    r"\b(\d+(?:\.\d+)+)\b",               # versiones como 118.0.5
    r"\b(\d{3,})\b",                        # códigos y números de 3 o más cifras
    r"\b(" + "|".join(NOMBRES_DE_PLATAFORMAS) + r")\b",
]


def _normalizar(texto):
    """Minúsculas, comillas rectas y espacios simples, para comparar sin falsos positivos."""
    texto = texto.replace("“", '"').replace("”", '"').replace("’", "'")
    return " ".join(texto.lower().split())


def datos_concretos(texto):
    """Devuelve los datos concretos de los campos verificables, sin los [Completar: ...]."""
    datos = []
    for nombre, contenido in leer_campos(texto):
        if nombre not in CAMPOS_VERIFICABLES:
            continue
        contenido = re.sub(r"\[Completar[^\]]*\]", " ", contenido)
        for patron in _DATOS_CONCRETOS:
            for dato in re.findall(patron, contenido):
                dato = dato.strip().rstrip(".,;:")
                if dato and dato not in datos:
                    datos.append(dato)
    return datos


# Adjuntos que la Evidencia no puede dar por hechos si el QA no los mencionó.
TIPOS_DE_ADJUNTO = ["captura", "screenshot", "video", "grabación", "stack trace", "har"]


def adjuntos_no_aportados(texto, fuente):
    """Adjuntos que la Evidencia da por hechos (fuera de [Completar]) y el QA no mencionó."""
    evidencia = re.sub(r"\[Completar[^\]]*\]", " ", campo(texto, "Evidencia"))
    evidencia = _normalizar(evidencia)
    return [a for a in TIPOS_DE_ADJUNTO
            if re.search(rf"\b{a}", evidencia) and not re.search(rf"\b{a}", fuente)]


def regla_b08(texto, entrada):
    """Nada de lo que afirma el reporte puede faltar en lo que contó el QA.

    Revisa los datos concretos (URLs, rutas, códigos, versiones, comillas, plataformas)
    y los adjuntos que la Evidencia da por hechos (capturas, videos, stack traces).
    """
    fuente = _normalizar(entrada or "")
    errores = [f'Dato que no aparece en lo que contó el QA: "{dato}"'
               for dato in datos_concretos(texto) if _normalizar(dato) not in fuente]
    errores += [f'La Evidencia menciona "{a}", pero el QA no la aportó: va como [Completar: adjuntar ...]'
                for a in adjuntos_no_aportados(texto, fuente)]
    return errores


REGLAS = {
    "B01": regla_b01,
    "B02": regla_b02,
    "B03": regla_b03,
    "B04": regla_b04,
    "B05": regla_b05,
    "B06": regla_b06,
    "B07": regla_b07,
}


def validar_reporte(texto, entrada):
    """Aplica todas las reglas al reporte. Devuelve {regla: [errores]}.

    entrada es lo que contó el QA: la usa B08 para detectar datos inventados.
    """
    errores = {nombre: regla(texto) for nombre, regla in REGLAS.items()}
    errores["B08"] = regla_b08(texto, entrada)
    return errores
