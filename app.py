"""Herramientas de QA con IA: casos Gherkin y reportes de bugs (Streamlit)."""
import os

import anthropic
import streamlit as st

from aclaraciones import armar_historia, hay_respuestas, separar_preguntas
from reporte import armar_entrada
from reporte_validador import validar_reporte
from validador import validar_texto

# En modo prueba (tests de Playwright) se usa el simulador en lugar de la IA real.
if os.environ.get("MODO_PRUEBA") == "1":
    from simulador import generar_con_revision, generar_reporte_con_revision
else:
    from generador import generar_con_revision
    from reporte import generar_reporte_con_revision

st.title("Generador de casos Gherkin y reportes de bugs")


def ejecutar(clave, funcion, texto):
    """Genera con la función indicada y guarda el resultado en la sesión.

    clave separa el estado de cada pestaña ("gherkin" o "bug").
    Devuelve True si salió bien.
    """
    st.session_state.pop(f"{clave}_resultado", None)
    try:
        with st.status("Trabajando...", expanded=True) as estado:
            st.session_state[f"{clave}_resultado"] = funcion(texto, avisar=st.write)
            st.session_state[f"{clave}_entrada"] = texto
            # Cada ronda de preguntas usa claves nuevas para que los cuadros arranquen vacíos.
            st.session_state[f"{clave}_ronda"] = st.session_state.get(f"{clave}_ronda", 0) + 1
            estado.update(label="Listo", state="complete", expanded=False)
        return True
    except (anthropic.APITimeoutError, TimeoutError):
        st.error("La IA tardó demasiado en responder. Probá de nuevo en un momento.")
    except anthropic.AuthenticationError:
        st.error("La clave de la API no es válida. Revisá el archivo .env.")
    except anthropic.APIError as error:
        st.error(f"No se pudo generar. Error de la API: {error}")
    except KeyError:
        st.error("Falta CLAUDE_MODEL en el archivo .env.")
    return False


def mostrar_preguntas(clave, funcion, resultado, aviso):
    """Muestra las preguntas de aclaración con un cuadro de respuesta para cada una."""
    st.warning(aviso)
    preguntas = separar_preguntas(resultado["contenido"])
    ronda = st.session_state.get(f"{clave}_ronda", 0)

    if preguntas:
        st.write("Respondé las que sepas. Las que dejes vacías se completan sin inventar datos.")
        respuestas = [
            st.text_input(f"Pregunta {numero}: {pregunta}", key=f"{clave}_respuesta_{ronda}_{numero}")
            for numero, pregunta in enumerate(preguntas, start=1)
        ]
    else:
        # Si las preguntas no vienen numeradas, se muestran tal cual con un solo cuadro.
        st.markdown(resultado["contenido"])
        preguntas = [resultado["contenido"]]
        respuestas = [st.text_area("Tus respuestas", key=f"{clave}_respuesta_{ronda}_todas")]

    if st.button("Generar con respuestas", key=f"{clave}_responder"):
        if not hay_respuestas(respuestas):
            st.error("Respondé al menos una pregunta antes de generar.")
        else:
            texto = armar_historia(st.session_state[f"{clave}_entrada"], preguntas, respuestas)
            if ejecutar(clave, funcion, texto):
                st.rerun()  # vuelve a dibujar la pantalla con el nuevo resultado


def mostrar_revision(resultado, validaciones):
    """Muestra los problemas que quedaron y la validación automática."""
    graves = [p for p in resultado["problemas"] if p.get("gravedad") == "alta"]
    menores = [p for p in resultado["problemas"] if p.get("gravedad") != "alta"]

    st.subheader("Revisión")
    st.caption(f"Intentos usados: {len(resultado['historial'])} de 3")
    if not resultado["revisor_ok"]:
        st.warning("El revisor IA no respondió en el formato esperado: la revisión de contenido está incompleta.")
    if graves:
        st.error("Quedaron problemas sin resolver. Revisalos antes de usar el resultado:")
        for p in graves:
            st.markdown(f"- **{p['regla']}**: {p['detalle']}")
    else:
        st.success("Sin problemas graves.")
    if menores:
        with st.expander(f"Sugerencias menores ({len(menores)})"):
            for p in menores:
                st.markdown(f"- **{p['regla']}**: {p['detalle']}")

    st.subheader("Validación automática")
    for regla, errores in validaciones.items():
        if errores:
            st.error(f"{regla}: " + " | ".join(errores))
        else:
            st.success(f"{regla}: OK")


def mostrar_historial(resultado):
    with st.expander("Historial de intentos"):
        for paso in resultado["historial"]:
            st.markdown(f"**Intento {paso['intento']}**: {len(paso['problemas'])} problema(s)")
            for p in paso["problemas"]:
                st.markdown(f"- {p['regla']} ({p.get('gravedad', '?')}): {p['detalle']}")


pestana_gherkin, pestana_bug = st.tabs(["Casos Gherkin", "Reporte de bug"])

# --- Casos Gherkin -----------------------------------------------------------
with pestana_gherkin:
    st.write("Pegá una historia de usuario y obtené escenarios en Gherkin.")
    historia = st.text_area("Historia de usuario", height=200)

    if st.button("Generar"):
        if not historia.strip():
            st.session_state.pop("gherkin_resultado", None)
            st.error("Pegá una historia de usuario antes de generar.")
        else:
            ejecutar("gherkin", generar_con_revision, historia)

    # El resultado se guarda en la sesión para que no desaparezca al descargar.
    resultado = st.session_state.get("gherkin_resultado")

    if resultado and resultado["tipo"] == "preguntas":
        mostrar_preguntas("gherkin", generar_con_revision, resultado,
                          "La historia necesita aclaraciones antes de generar escenarios:")

    if resultado and resultado["tipo"] == "feature":
        feature = resultado["contenido"]
        mostrar_revision(resultado, validar_texto(feature))

        if "Aclaraciones:" in st.session_state.get("gherkin_entrada", ""):
            with st.expander("Historia usada (con tus respuestas)"):
                st.text(st.session_state["gherkin_entrada"])

        st.subheader("Escenarios")
        st.code(feature, language="gherkin", wrap_lines=True)
        st.download_button(
            "Descargar .feature",
            data=feature,
            file_name="casos.feature",
            mime="text/plain",
        )
        mostrar_historial(resultado)

# --- Reporte de bug ----------------------------------------------------------
with pestana_bug:
    st.write("Contá el bug con tus palabras. Si tenés un log o un error de consola, pegalo abajo.")
    descripcion = st.text_area("Descripción del bug", height=200)
    log = st.text_area("Log o error de consola (opcional)", height=120)

    if st.button("Generar reporte"):
        if not descripcion.strip():
            st.session_state.pop("bug_resultado", None)
            st.error("Describí el bug antes de generar el reporte.")
        else:
            ejecutar("bug", generar_reporte_con_revision, armar_entrada(descripcion, log))

    resultado = st.session_state.get("bug_resultado")

    if resultado and resultado["tipo"] == "preguntas":
        mostrar_preguntas("bug", generar_reporte_con_revision, resultado,
                          "Faltan datos esenciales para redactar el reporte:")

    if resultado and resultado["tipo"] == "reporte":
        reporte = resultado["contenido"]
        mostrar_revision(resultado, validar_reporte(reporte, st.session_state.get("bug_entrada", "")))

        st.subheader("Reporte")
        # Markdown une las líneas seguidas: se fuerza un salto por línea, y cada campo
        # va en su propio párrafo para que no quede metido dentro de la lista de pasos.
        # Los casos de regresión se muestran aparte, como código Gherkin.
        texto, _, casos = reporte.partition("**Casos de regresión:**")
        st.markdown(texto.strip().replace("\n", "  \n").replace("  \n**", "\n\n**"))
        if casos.strip():
            st.markdown("**Casos de regresión:**")
            st.code(casos.strip("\n"), language="gherkin", wrap_lines=True)
        with st.expander("Texto para copiar (Markdown)"):
            st.code(reporte, language="markdown", wrap_lines=True)
        st.download_button(
            "Descargar reporte",
            data=reporte,
            file_name="reporte_bug.md",
            mime="text/markdown",
        )
        mostrar_historial(resultado)
