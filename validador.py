"""Validador de archivos .feature según la checklist de calidad.

Reglas que verifica (las que no necesitan IA):
  R04 - Primera línea "# language: es" y palabras clave en español
  R05 - Sintaxis de Gherkin válida (usa el parser oficial)
  R07 - Solo etiquetas permitidas: @smoke, @regresion, @negativo
  R08 - Al menos un escenario @smoke y uno @negativo
  R20 - Los escenarios citados en la cobertura existen en el archivo

Uso:
  python validador.py ejemplos              (valida todos los .feature de la carpeta)
  python validador.py ejemplos/hu01.feature (valida un solo archivo)
"""
import re
import sys
from pathlib import Path

ETIQUETAS_PERMITIDAS = {"@smoke", "@regresion", "@negativo"}

PALABRAS_EN_INGLES = (
    "Feature:", "Background:", "Scenario:", "Scenario Outline:",
    "Examples:", "Given ", "When ", "Then ", "And ", "But ",
)


def regla_r04(texto):
    """Primera línea con el idioma y sin palabras clave en inglés."""
    errores = []
    lineas = [l.strip() for l in texto.splitlines() if l.strip()]
    if not lineas or lineas[0] != "# language: es":
        errores.append('La primera línea no es "# language: es"')
    for numero, linea in enumerate(texto.splitlines(), start=1):
        if linea.strip().startswith(PALABRAS_EN_INGLES):
            errores.append(f"Línea {numero}: palabra clave en inglés -> {linea.strip()}")
    return errores


def regla_r05(texto):
    """La sintaxis de Gherkin es válida según el parser oficial."""
    try:
        from gherkin.parser import Parser
        from gherkin.token_scanner import TokenScanner
    except ImportError:
        return ["No se pudo evaluar: falta instalar gherkin-official"]
    try:
        Parser().parse(TokenScanner(texto))
    except Exception as error:  # el parser lanza distintos tipos de error
        return [f"Sintaxis inválida: {error}"]
    return []


def etiquetas_del_archivo(texto):
    """Devuelve todas las etiquetas (@algo) que aparecen en el archivo."""
    etiquetas = []
    for linea in texto.splitlines():
        if linea.strip().startswith("@"):
            etiquetas += re.findall(r"@[\w-]+", linea)
    return etiquetas


def regla_r07(texto):
    """Solo se usan las etiquetas permitidas."""
    no_permitidas = sorted(set(etiquetas_del_archivo(texto)) - ETIQUETAS_PERMITIDAS)
    return [f"Etiqueta no permitida: {e}" for e in no_permitidas]


def regla_r08(texto):
    """Hay al menos un @smoke y un @negativo."""
    etiquetas = set(etiquetas_del_archivo(texto))
    errores = []
    for obligatoria in ("@smoke", "@negativo"):
        if obligatoria not in etiquetas:
            errores.append(f"Falta al menos un escenario {obligatoria}")
    return errores


def nombres_de_escenarios(texto):
    """Devuelve los nombres de todos los escenarios y esquemas del archivo."""
    nombres = set()
    for linea in texto.splitlines():
        linea = linea.strip()
        for clave in ("Esquema del escenario:", "Escenario:"):
            if linea.startswith(clave):
                nombres.add(linea[len(clave):].strip())
                break
    return nombres


def regla_r20(texto):
    """Cada escenario mencionado en la tabla de cobertura existe en el archivo."""
    existentes = nombres_de_escenarios(texto)
    errores = []
    for linea in texto.splitlines():
        if not linea.strip().startswith("# Cobertura:") or "->" not in linea:
            continue
        for nombre in linea.split("->", 1)[1].split(";"):
            nombre = re.sub(r"\s*\(.*\)\s*$", "", nombre).strip()  # quita "(límites ...)"
            if not nombre or nombre.startswith(("No aplica", "No hay")):
                continue
            if nombre not in existentes:
                errores.append(f'La cobertura menciona un escenario que no existe: "{nombre}"')
    return errores


REGLAS = {
    "R04": regla_r04,
    "R05": regla_r05,
    "R07": regla_r07,
    "R08": regla_r08,
    "R20": regla_r20,
}


def validar_texto(texto):
    """Aplica todas las reglas a un texto. Devuelve {regla: [errores]}."""
    return {nombre: regla(texto) for nombre, regla in REGLAS.items()}


def validar_archivo(ruta):
    """Aplica todas las reglas a un archivo. Devuelve {regla: [errores]}."""
    return validar_texto(Path(ruta).read_text(encoding="utf-8"))


def main():
    if len(sys.argv) != 2:
        print("Uso: python validador.py <carpeta o archivo .feature>")
        sys.exit(2)

    destino = Path(sys.argv[1])
    archivos = sorted(destino.glob("*.feature")) if destino.is_dir() else [destino]
    if not archivos:
        print(f"No se encontraron archivos .feature en {destino}")
        sys.exit(2)

    total_fallas = 0
    for archivo in archivos:
        print(f"\n{archivo.name}")
        for regla, errores in validar_archivo(archivo).items():
            if errores:
                total_fallas += 1
                print(f"  FALLA {regla}")
                for error in errores:
                    print(f"        - {error}")
            else:
                print(f"  OK    {regla}")

    print(f"\nArchivos: {len(archivos)} | Reglas con fallas: {total_fallas}")
    sys.exit(1 if total_fallas else 0)


if __name__ == "__main__":
    main()
