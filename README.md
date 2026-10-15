# Generador de casos Gherkin y reportes de bugs con IA

[![Tests](https://github.com/Gikza/gherkin-generator-ai/actions/workflows/tests.yml/badge.svg)](https://github.com/Gikza/gherkin-generator-ai/actions/workflows/tests.yml)

**[Probar la demo online](https://gherkin-generator-gikza.streamlit.app)**: resultados reales de la IA, sin instalar nada.

Herramienta para el trabajo diario de un QA, con la API de Claude. Tiene dos funciones:

1. **Casos Gherkin:** genera escenarios de prueba en Gherkin (español) a partir de una historia de usuario.
2. **Reportes de bugs:** redacta un reporte claro y reproducible, listo para cualquier herramienta de gestión (Jira, Azure DevOps, Trello, etc.), a partir de lo que cuenta el QA y un log opcional.

Lo que la diferencia es que **no confía en la salida de la IA**: cada resultado pasa por validaciones automáticas, un revisor IA y un ciclo de corrección antes de entregarse. Las dos funciones usan **el mismo ciclo**; solo cambian las reglas.

> Proyecto de portfolio en desarrollo. Autora: Gikza, QA con más de 5 años de experiencia, en camino a Automation QA con IA.

## Qué hace

- Pegás una historia de usuario y obtenés un archivo `.feature` listo para Cucumber, con camino feliz, casos negativos y casos borde.
- Si la historia es ambigua (por ejemplo, "la búsqueda debe ser rápida"), **pregunta en lugar de inventar requisitos**.
- Las preguntas se **responden en la misma pantalla**: la herramienta agrega las respuestas a la historia y vuelve a generar. Las preguntas que quedan sin responder se toman como supuestos y se anotan en el archivo.
- Muestra los supuestos que tomó, la tabla de cobertura por criterio y los problemas que quedaron sin resolver.

### Reportes de bugs

- Escribís el bug con tus palabras y, si querés, pegás un log o error de consola.
- Si faltan datos esenciales (qué pasó, qué debería pasar o cómo se llega al error), **pregunta**. Lo que no es esencial, como el navegador o la versión, queda marcado como `[Completar: ...]`: **nunca se inventa**.
- El reporte incluye título con módulo, entorno, precondiciones, pasos, resultado esperado y actual, severidad justificada, frecuencia, evidencia y **1 o 2 casos de regresión en Gherkin** para verificar el arreglo.

## Cómo funciona

```
Historia ─► ¿Faltan datos? ──sí──► Preguntas ──► Respuestas en pantalla
   ▲             │ no                                     │
   └─────────────┼──────── historia + aclaraciones ◄──────┘
                 │
                 ▼
             Generar (IA) ─► Validar (Python) + Revisar (IA)
                 ▲                      │
                 │            ¿Problemas graves?
                 └──── sí (máx. 2) ─────┤
                                        │ no
                                        ▼
                                 .feature final
```

La calidad se controla con una **checklist de 23 reglas**, armada a partir de revisar a mano las salidas de la IA. Cada regla se verifica en la capa más barata que puede detectarla:

| Capa | Reglas | Ejemplos |
|---|---|---|
| Python + parser oficial de Gherkin | R04, R05, R07, R08, R20 | Sintaxis válida, idioma, etiquetas permitidas, cobertura que cita escenarios reales |
| Revisor IA | R02, R06, R10, R11, R12, R14, R21, R22, R23 | Antecedentes contradictorios, precondiciones dentro de un `Cuando`, requisitos inventados |

La **gravedad** de cada regla la define una tabla fija en Python, no la IA, para que el comportamiento sea predecible.

Los reportes de bugs tienen sus propias reglas, con el mismo criterio de capas:

| Capa | Reglas | Ejemplos |
|---|---|---|
| Python | B01 a B08 | Campos obligatorios y en orden, título con `[Módulo]` y hasta 80 caracteres, severidad de la escala con justificación, frecuencia válida, al menos 2 pasos, esperado distinto de actual, 1 o 2 casos de regresión y **datos inventados (B08)** |
| Revisor IA | B10 a B15 | Datos inventados, severidad incoherente, pasos no reproducibles, resultado actual que no copia el error, log sin explicar |

**B08 verifica con código, no con la IA, que el reporte no invente datos.** Cada dato concreto (URLs, rutas, códigos, versiones, textos entre comillas, navegadores y sistemas) tiene que aparecer en lo que contó el QA, y la Evidencia no puede dar por hechas capturas, videos o stack traces que el QA no aportó: van como `[Completar: adjuntar ...]`. No revisa el resultado esperado, las notas ni los casos de regresión, porque describen lo que debería pasar o lo que se sospecha.

La **severidad (B11) es solo una sugerencia**: en una prueba, el revisor obligó a bajar un bug de Alta a Media en un caso discutible. La severidad depende del contexto del negocio, así que la decide la QA, no la IA.

## Lo que aprendí probando la IA

- **Validación en verde no es calidad.** La primera salida real pasó las 4 validaciones de forma y tenía 4 errores de contenido, entre ellos una tabla de cobertura que citaba un escenario que no existía.
- **Ajustar el prompt funcionó y lo medí.** Después del ajuste, en 3 ejecuciones con la misma historia, los 4 tipos de error no volvieron a aparecer.
- **La salida no es determinística.** La misma historia generó 6, 10 y 10 escenarios, con cobertura distinta. Por eso los controles verifican *propiedades* (cobertura, límites, etiquetas) y no comparan contra un texto fijo.
- **Dos IA pueden no compartir el mismo criterio.** Al responder que el cupón lo genera "un administrador", el generador agregó casos de permisos (rol denegado, acceso por URL directa, sin sesión) y el revisor los marcó como requisitos inventados. La solución fue definir el criterio una sola vez (`CRITERIO_PERMISOS`) y usarlo en los dos prompts, con un test que lo verifica.
- **La corrección también puede inventar.** En un reporte de bug, al corregir, la IA afirmó que había capturas y un stack trace que el QA nunca dio. El revisor lo detectó (B10) y se corrigió en el intento siguiente. Una sola pasada de la IA no alcanza, ni siquiera cuando corrige.
- **Una IA controlando a otra no alcanza.** En otra prueba, el revisor dejó pasar adjuntos inventados. Además, en LinkedIn me preguntaron cómo decide la herramienta que un dato no lo sabe: lo decidía el modelo. Por eso agregué B08, que lo verifica con código contra lo que pegó el QA.
- **No todo lo tiene que decidir la IA.** El revisor obligó a cambiar la severidad de un bug de Alta a Media en un caso discutible. Ahora la severidad es solo una sugerencia y la decide la QA.
- **El revisor también se equivoca.** Clasificó el mismo problema con gravedades distintas entre intentos y marcó un posible falso positivo. Ningún componente es confiable por separado: la combinación de capas y la revisión humana final es lo que da calidad.

## Estructura

| Archivo | Función |
|---|---|
| `app.py` | Interfaz web (Streamlit) |
| `aclaraciones.py` | Une la historia con las respuestas a las preguntas (sin IA) |
| `reporte.py` | Reportes de bugs: arma la entrada y reutiliza el ciclo de `generador.py` |
| `reporte_prompt.py` | Instrucciones del generador y del revisor de reportes, y su tabla de gravedad |
| `reporte_validador.py` | Reglas B01 a B08, verificables con Python (B08: datos inventados) |
| `generador.py` | Generación y ciclo de revisión y corrección (compartido por las dos funciones) |
| `prompt.py` | Instrucciones del generador (checklist como *system prompt*) |
| `revisor.py` | Revisor IA y tabla de gravedad |
| `validador.py` | Reglas verificables con Python; también funciona por línea de comandos |
| `evaluar.py` | Evaluación con la IA real sobre el set de casos de `evaluacion/` |
| `uso.py` | Cuenta las llamadas y los tokens de cada generación |
| `demo.py` | Modo demo: resultados reales grabados en `demo/ejemplos.json` |
| `simulador.py` | Respuestas fijas de la IA para los tests de interfaz |
| `e2e/` | Tests end-to-end con Playwright (TypeScript) |
| `tests/` | Tests unitarios (pytest) |
| `.github/workflows/` | Integración continua con GitHub Actions |
| `ejemplos/` | Archivos `.feature` de referencia |
| `pruebas_validador/` | Archivo roto a propósito para probar el validador |

## Modo demo

Demo publicada en **[gherkin-generator-gikza.streamlit.app](https://gherkin-generator-gikza.streamlit.app)** (Streamlit Community Cloud). Si estuvo un tiempo sin visitas, la primera carga puede tardar unos segundos mientras se reactiva.

Si la app arranca sin clave de la API (por ejemplo, publicada en Streamlit Community Cloud), entra en **modo demo**: muestra resultados **reales** de la IA, grabados durante la evaluación, con su validación automática y su historial de correcciones. No llama a la IA, así que no gasta créditos. Los ejemplos se graban con:

```bash
python evaluar.py --guardar-demo
```

## Cómo ejecutarlo

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env          # completar ANTHROPIC_API_KEY y CLAUDE_MODEL
streamlit run app.py
```

Validar archivos `.feature` sin la interfaz:

```bash
python validador.py ejemplos
```

## Tests unitarios (pytest)

81 tests:

- **Validador de casos Gherkin (14):** cada regla con casos que deben pasar y casos que deben fallar, incluido un archivo roto a propósito y el `.feature` que usa el simulador.
- **Aclaraciones (7):** separar las preguntas de la IA y armar la historia con las respuestas, incluidas las preguntas sin responder.
- **Prompts (5):** generador y revisor comparten los mismos criterios de permisos, longitud y supuestos, y la severidad del reporte es solo una sugerencia.
- **Validador de reportes (31):** cada regla B01 a B08 con casos que pasan y que fallan, incluido el caso real de adjuntos inventados.
- **Modo demo (7):** busca el resultado grabado de cada ejemplo, avisa si la entrada no es un ejemplo y guarda solo ejecuciones aprobadas.
- **Evaluación (10):** cómo se califica cada resultado y cómo se arma el resumen, con resultados falsos.
- **Ciclo de revisión (7):** con funciones falsas, sin llamar a la IA: no corrige si no hay problemas graves, respeta el máximo de correcciones, se queda con la última versión si la IA responde con preguntas y le pasa al validador lo que contó el QA.

```bash
pytest -v
```

## Evaluación con la IA real

Los tests no llaman a la IA. Para medir la calidad de lo que genera de verdad, hay un **set fijo de 10 casos** (`evaluacion/casos.json`): historias completas, historias ambiguas, bugs con log, bugs sin datos esenciales, bugs sin entorno y bugs donde el QA sí aporta evidencia. Cada caso define qué tipo de resultado se espera y qué textos no deberían aparecer porque serían inventados.

```bash
python evaluar.py                    # todos los casos, una vez
python evaluar.py --repeticiones 3   # para medir la variabilidad
python evaluar.py --casos G01,R01    # solo algunos casos
```

El script mide, por ejecución y en total: casos aprobados, problemas graves en el primer intento y al final, datos inventados detectados por código (B08), intentos, tiempo, llamadas a la API y tokens. Guarda el detalle en JSON y un resumen en Markdown en `evaluacion/resultados/`. No corre en GitHub Actions porque gasta créditos de la API.

**Primera evaluación** (15/10/2026, `claude-haiku-5-5`, 10 casos × 1 ejecución, [detalle](evaluacion/resultados/2026-10-15_1801.md)):

| Métrica | Resultado |
|---|---|
| Casos aprobados | 10 de 10 |
| Historias y bugs ambiguos que terminaron en preguntas, sin inventar | 3 de 3 |
| Resultados con problemas graves en el primer intento | 3 de 7 |
| Resultados con problemas graves al final | 0 de 7 |
| Intentos promedio / tiempo promedio | 1,7 / 44 s |

El ciclo de revisión corrigió todos los problemas graves del primer intento: entre ellos, un requisito inventado en una historia (R23) y datos inventados en un reporte (B10).

**Segunda corrida** (mismo día y mismos casos, [detalle](evaluacion/resultados/2026-10-15_1821_recalificado.md)): **9 de 10**. Dejó dos aprendizajes:

- **La evaluación también se testea.** Marcó como inventado "iOS" porque lo encontró dentro de "pasos prev*ios*". Corregí el chequeo para que busque palabras completas y agregué `--recalificar`, que vuelve a calificar una corrida guardada sin llamar a la IA.
- **Choque entre reglas (resuelto).** En "recuperar contraseña", la regla que pide probar la longitud máxima de los campos llevó a la IA a inventar un máximo de 128 caracteres que la historia no define, y el revisor lo marcó como requisito inventado (R23). Como con los permisos, definí un criterio común (`CRITERIO_LONGITUD`): el máximo se prueba solo si la historia lo define; si no, queda como `# Pregunta abierta`. En la verificación ([detalle](evaluacion/resultados/2026-10-15_1901.md)), las dos ejecuciones de ese caso dejaron la pregunta abierta en lugar de inventar el límite. Una de ellas falló por otro motivo: supuestos que agregan comportamiento nuevo (por ejemplo, "el enlace es de un solo uso"), que el revisor marcó como requisitos inventados. Lo resolví con el mismo patrón (`CRITERIO_SUPUESTOS`): un supuesto solo aclara algo que la historia ya menciona; si agrega comportamiento, queda como `# Pregunta abierta` y no se prueba. Verificación ([detalle](evaluacion/resultados/2026-10-15_1912.md)): 4 de 4, con "recuperar contraseña" y "cupón" dos veces cada uno.

## Integración continua

En cada `push`, **GitHub Actions** ejecuta los tests unitarios y los de Playwright en la nube. Si algún test de interfaz falla, guarda el reporte de Playwright para revisarlo.

## Tests de interfaz (Playwright + TypeScript)

12 tests end-to-end que cubren las dos pestañas: validación de la entrada, respuestas de la IA, preguntas de aclaración, descargas y manejo de errores.

```bash
cd e2e
npm install
npx playwright test
```

Los tests **no llaman a la IA real**: Playwright levanta la app en modo prueba (`MODO_PRUEBA=1`) y un simulador devuelve respuestas fijas. Así los tests son gratis, rápidos y predecibles, y pueden provocar errores a propósito, como una IA que tarda demasiado. La calidad de lo que genera la IA se controla por separado, con el validador y el revisor.

| Grupo | Qué se prueba |
|---|---|
| Validación de la entrada | Historia vacía y solo con espacios |
| Respuesta de la IA | Preguntas ante historias ambiguas, generación con validación, descarga |
| Respuestas a las preguntas | Generar después de responder; exigir al menos una respuesta |
| Reporte de bug | Descripción vacía, generación con validación, descarga y preguntas por datos esenciales |
| Manejo de errores | Mensaje claro si la IA tarda demasiado |

## Próximos pasos

- [x] Tests de interfaz con **Playwright**
- [x] Tests unitarios del validador con `pytest`
- [x] Integración continua con GitHub Actions
- [x] Responder las preguntas de aclaración desde la misma pantalla
- [x] Generación de reportes de bugs (segunda funcionalidad)

## Stack

Python · Streamlit · API de Claude · gherkin-official · Gherkin/BDD · Playwright · TypeScript · pytest · GitHub Actions
