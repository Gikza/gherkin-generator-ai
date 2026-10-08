# Generador de casos Gherkin con IA

Herramienta que genera escenarios de prueba en **Gherkin (español)** a partir de una historia de usuario, usando la API de Claude. Lo que la diferencia es que **no confía en la salida de la IA**: cada resultado pasa por validaciones automáticas, un revisor IA y un ciclo de corrección antes de entregarse.

> Proyecto de portfolio en desarrollo. Autora: Gikza, QA con más de 5 años de experiencia, en camino a Automation QA con IA.

## Qué hace

- Pegás una historia de usuario y obtenés un archivo `.feature` listo para Cucumber, con camino feliz, casos negativos y casos borde.
- Si la historia es ambigua (por ejemplo, "la búsqueda debe ser rápida"), **pregunta en lugar de inventar requisitos**.
- Muestra los supuestos que tomó, la tabla de cobertura por criterio y los problemas que quedaron sin resolver.

## Cómo funciona

```
Historia ─► ¿Faltan datos? ──sí──► Preguntas de aclaración
                 │ no
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

## Lo que aprendí probando la IA

- **Validación en verde no es calidad.** La primera salida real pasó las 4 validaciones de forma y tenía 4 errores de contenido, entre ellos una tabla de cobertura que citaba un escenario que no existía.
- **Ajustar el prompt funcionó y lo medí.** Después del ajuste, en 3 ejecuciones con la misma historia, los 4 tipos de error no volvieron a aparecer.
- **La salida no es determinística.** La misma historia generó 6, 10 y 10 escenarios, con cobertura distinta. Por eso los controles verifican *propiedades* (cobertura, límites, etiquetas) y no comparan contra un texto fijo.
- **El revisor también se equivoca.** Clasificó el mismo problema con gravedades distintas entre intentos y marcó un posible falso positivo. Ningún componente es confiable por separado: la combinación de capas y la revisión humana final es lo que da calidad.

## Estructura

| Archivo | Función |
|---|---|
| `app.py` | Interfaz web (Streamlit) |
| `generador.py` | Generación, ciclo de revisión y corrección |
| `prompt.py` | Instrucciones del generador (checklist como *system prompt*) |
| `revisor.py` | Revisor IA y tabla de gravedad |
| `validador.py` | Reglas verificables con Python; también funciona por línea de comandos |
| `ejemplos/` | Archivos `.feature` de referencia |
| `pruebas_validador/` | Archivo roto a propósito para probar el validador |

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

## Próximos pasos

- [ ] Tests de interfaz con **Playwright**
- [ ] Tests unitarios del validador con `pytest`
- [ ] Integración continua con GitHub Actions
- [ ] Responder las preguntas de aclaración desde la misma pantalla
- [ ] Generación de reportes de bugs (segunda funcionalidad)

## Stack

Python · Streamlit · API de Claude · gherkin-official · Gherkin/BDD
