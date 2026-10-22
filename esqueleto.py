"""De Gherkin a Playwright: arma el esqueleto de un proyecto de tests a partir de un .feature.

Usa playwright-bdd, que corre los .feature con Playwright + TypeScript. Genera una definición
de paso por cada paso distinto del archivo, con sus parámetros, pero SIN lógica: cada paso
queda pendiente. Es código, no IA, a propósito: sin conocer la página real, cualquier
selector sería inventado. La QA completa los pasos con la aplicación delante.
"""
import io
import json
import re
import zipfile

from gherkin.parser import Parser
from gherkin.token_scanner import TokenScanner

# Palabra clave de Gherkin → función de playwright-bdd. "Y" y "Pero" heredan la anterior.
FUNCION_POR_TIPO = {"Context": "Given", "Action": "When", "Outcome": "Then"}
FUNCION_POR_PALABRA = {"dado": "Given", "dada": "Given", "dados": "Given", "dadas": "Given",
                       "given": "Given", "cuando": "When", "when": "When",
                       "entonces": "Then", "then": "Then"}

# Partes de un paso que se convierten en parámetros (Cucumber Expressions).
_PARAMETROS = re.compile(
    r'(?P<comillas>"[^"]*")'           # "texto" o "<param>"  → {string}
    r"|(?P<param><[^<>\s]+>)"          # <param> sin comillas  → {}
    # Número suelto: 24 → {int}, -5 → {int}, 0.5 → {float}. Formatos como $1.000,00 o
    # fechas 2026-10-22 quedan literales: partirlos en varios números genera ambigüedades.
    r"|(?P<numero>(?<![\w.,/-])-?\d(?:[\d.,]*\d)?(?![\w/-]|[.,]\d))"
)
TIPOS_TS = {"string": ("texto", "string"), "": ("valor", "string"),
            "float": ("decimal", "number"), "int": ("numero", "number")}
_ESPECIALES = re.compile(r"([\\(){}/])")  # se escapan en una Cucumber Expression


def _escapar(literal):
    return _ESPECIALES.sub(r"\\\1", literal)


def a_expresion(texto):
    """Convierte el texto de un paso en Cucumber Expression. Devuelve (expresion, tipos)."""
    partes, tipos, ultimo = [], [], 0
    for m in _PARAMETROS.finditer(texto):
        tipo = {"comillas": "string", "param": ""}.get(m.lastgroup)
        if m.lastgroup == "numero":
            if re.fullmatch(r"-?\d+", m.group()):
                tipo = "int"
            elif re.fullmatch(r"-?\d+\.\d+", m.group()) and not re.fullmatch(r"-?\d{1,3}(\.\d{3})+", m.group()):
                # 0.5 es decimal; 20.000 es "veinte mil" con punto de miles: queda literal
                tipo = "float"
            else:
                continue  # número con formato: queda como texto literal
        partes.append(_escapar(texto[ultimo:m.start()]))
        partes.append("{" + tipo + "}")
        tipos.append(tipo)
        ultimo = m.end()
    partes.append(_escapar(texto[ultimo:]))
    return "".join(partes), tipos


def coincide(expresion, texto):
    """¿La expresión coincide con un paso concreto? Aproxima a Cucumber (para los tests)."""
    patron, i = "", 0
    while i < len(expresion):
        if expresion[i] == "\\":
            patron += re.escape(expresion[i + 1])
            i += 2
            continue
        if expresion[i] == "{":
            fin = expresion.index("}", i)
            tipo = expresion[i + 1:fin]
            patron += {"string": r'(?:"[^"]*"|\'[^\']*\')', "int": r"-?\d+", "float": r"-?\d*\.?\d+",
                       "": r".*"}[tipo]
            i = fin + 1
            continue
        patron += re.escape(expresion[i])
        i += 1
    return re.fullmatch(patron, texto) is not None


def leer_pasos(feature):
    """Lista de pasos del .feature: dict con funcion, texto, escenario y argumento (tabla/docstring)."""
    documento = Parser().parse(TokenScanner(feature))
    hijos = list(documento["feature"]["children"])
    pasos = []
    while hijos:
        hijo = hijos.pop(0)
        if "rule" in hijo:
            hijos = list(hijo["rule"]["children"]) + hijos
            continue
        bloque = hijo.get("background") or hijo.get("scenario")
        nombre = bloque.get("name") or bloque["keyword"]
        anterior = "Given"
        for paso in bloque["steps"]:
            funcion = FUNCION_POR_TIPO.get(paso.get("keywordType"))
            if funcion is None:
                funcion = FUNCION_POR_PALABRA.get(paso["keyword"].strip().lower(), anterior)
            anterior = funcion
            argumento = "tabla" if "dataTable" in paso else "docstring" if "docString" in paso else None
            pasos.append({"funcion": funcion, "texto": paso["text"], "escenario": nombre,
                          "argumento": argumento, "ejemplos": bloque.get("examples", [])})
    return pasos


def textos_concretos(paso):
    """Textos del paso tal como se ejecutan: en un esquema, uno por fila de Ejemplos."""
    textos = []
    for ejemplos in paso["ejemplos"]:
        encabezado = [c["value"] for c in ejemplos.get("tableHeader", {}).get("cells", [])]
        for fila in ejemplos.get("tableBody", []):
            texto = paso["texto"]
            for clave, celda in zip(encabezado, fila["cells"]):
                texto = texto.replace(f"<{clave}>", celda["value"])
            textos.append(texto)
    return textos or [paso["texto"]]


def definiciones(feature):
    """Una definición por expresión distinta, en orden de aparición.

    Los esquemas se expanden fila por fila antes de convertir: un parámetro como
    "el turno <resultado>" puede valer frases enteras, y generalizarlo a "cualquier cosa"
    haría que la definición choque con otros pasos (ambigüedad que bddgen rechaza).
    Así, solo se vuelve parámetro lo que es un texto entre comillas o un número.
    """
    por_expresion = {}
    for paso in leer_pasos(feature):
        for texto in textos_concretos(paso):
            expresion, tipos = a_expresion(texto)
            d = por_expresion.setdefault(expresion, {"funcion": paso["funcion"], "expresion": expresion,
                                                      "tipos": tipos, "argumento": paso["argumento"],
                                                      "escenarios": [], "ejemplo": texto, "textos": []})
            if paso["escenario"] not in d["escenarios"]:
                d["escenarios"].append(paso["escenario"])
            if texto not in d["textos"]:
                d["textos"].append(texto)
    return _sin_duplicadas(list(por_expresion.values()))


def _sin_duplicadas(defs):
    """Si una definición ya cubre todos los pasos de otra, se queda solo la más general.

    Ejemplo: "pesa {int} kg" y "pesa {float} kg" chocan con "pesa 2 kg" ({float} acepta
    enteros); alcanza con la de {float}.
    """
    for d in list(defs):
        otras = [o for o in defs if o is not d]
        cubridora = next((o for o in otras if all(coincide(o["expresion"], t) for t in d["textos"])), None)
        if cubridora is not None:
            for e in d["escenarios"]:
                if e not in cubridora["escenarios"]:
                    cubridora["escenarios"].append(e)
            cubridora["textos"] += [t for t in d["textos"] if t not in cubridora["textos"]]
            defs.remove(d)
    return defs


def problemas_de_coincidencia(feature):
    """Pasos sin definición o con más de una (lo que bddgen rechazaría). Lista vacía = OK."""
    defs = definiciones(feature)
    problemas = []
    for paso in leer_pasos(feature):
        for texto in textos_concretos(paso):
            n = sum(coincide(d["expresion"], texto) for d in defs)
            if n != 1:
                problemas.append(f"{'Sin definición' if n == 0 else 'Ambiguo'}: {texto}")
    return sorted(set(problemas))


def _cadena_ts(texto):
    return "'" + texto.replace("\\", "\\\\").replace("'", "\\'") + "'"


def generar_pasos_ts(feature):
    """Contenido de steps/pasos.ts."""
    defs = definiciones(feature)
    usa_tabla = any(d["argumento"] == "tabla" for d in defs)
    lineas = [
        "// Generado a partir del .feature. Cada paso está PENDIENTE: completalo con Playwright.",
        "// No incluye selectores a propósito: sin ver la página real, serían inventados.",
        "import { createBdd" + (", DataTable" if usa_tabla else "") + " } from 'playwright-bdd';",
        "",
        "const { Given, When, Then } = createBdd();",
        "",
    ]
    for d in defs:
        argumentos, contadores = ["{ page }"], {}
        for tipo in d["tipos"]:
            nombre, tipo_ts = TIPOS_TS[tipo]
            contadores[nombre] = contadores.get(nombre, 0) + 1
            argumentos.append(f"{nombre}{contadores[nombre]}: {tipo_ts}")
        if d["argumento"] == "tabla":
            argumentos.append("tabla: DataTable")
        elif d["argumento"] == "docstring":
            argumentos.append("texto: string")
        escenarios = d["escenarios"][:3]
        extra = f" y {len(d['escenarios']) - 3} más" if len(d["escenarios"]) > 3 else ""
        lineas += [
            f"// Usado en: {'; '.join(escenarios)}{extra}",
            f"{d['funcion']}({_cadena_ts(d['expresion'])}, async ({', '.join(argumentos)}) => {{",
            "  // TODO: implementar con Playwright (por ejemplo, page.getByRole(...)).",
            f"  throw new Error({_cadena_ts('Paso pendiente: ' + d['ejemplo'])});",
            "});",
            "",
        ]
    return "\n".join(lineas)


CONFIG_TS = """import { defineConfig } from '@playwright/test';
import { defineBddConfig } from 'playwright-bdd';

// playwright-bdd convierte los .feature en tests de Playwright dentro de testDir.
const testDir = defineBddConfig({
  features: 'features/*.feature',
  steps: 'steps/*.ts',
});

export default defineConfig({
  testDir,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    // Completá la dirección de la aplicación que vas a probar.
    baseURL: process.env.BASE_URL,
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
});
"""

README_MD = """# Esqueleto de tests con Playwright

Generado por el [Generador de casos Gherkin](https://github.com/Gikza/gherkin-generator-ai)
a partir de `features/{nombre}.feature`.

- `features/`: el archivo `.feature` tal como lo generó la herramienta.
- `steps/pasos.ts`: una definición por cada paso distinto ({cantidad} en total), con sus
  parámetros. **Todos están pendientes**: fallan con "Paso pendiente" hasta que los completes.
- `playwright.config.ts`: configuración de Playwright + playwright-bdd.

## Cómo usarlo

```bash
npm install
npx playwright install chromium
npm test
```

`npm test` primero convierte los `.feature` en tests (`bddgen`) y después los corre.
Al principio todos fallan: es lo esperado. Completá cada paso en `steps/pasos.ts` con
Playwright y definí la dirección de la aplicación en la variable `BASE_URL`.
"""


def generar_esqueleto(feature, nombre="casos"):
    """Devuelve {ruta: contenido} con el proyecto completo."""
    pasos_ts = generar_pasos_ts(feature)
    cantidad = pasos_ts.count("throw new Error(")
    package = {
        "name": "esqueleto-playwright",
        "private": True,
        "scripts": {"bddgen": "bddgen", "test": "bddgen && playwright test"},
        # Versiones fijas y probadas juntas: con "^" npm instala un Playwright más nuevo
        # que playwright-bdd todavía no soporta, y bddgen falla al arrancar.
        "devDependencies": {"@playwright/test": "1.64.1", "playwright-bdd": "9.2.1"},
    }
    return {
        f"features/{nombre}.feature": feature,
        "steps/pasos.ts": pasos_ts,
        "playwright.config.ts": CONFIG_TS,
        "package.json": json.dumps(package, indent=2) + "\n",
        "README.md": README_MD.replace("{nombre}", nombre).replace("{cantidad}", str(cantidad)),
        ".gitignore": "node_modules/\n.features-gen/\ntest-results/\nplaywright-report/\n",
    }


def empaquetar(archivos, carpeta="esqueleto-playwright"):
    """Arma un .zip en memoria con los archivos dentro de una carpeta."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_:
        for ruta, contenido in archivos.items():
            zip_.writestr(f"{carpeta}/{ruta}", contenido)
    return buffer.getvalue()
