"""Generador de casos Gherkin: interfaz web con Streamlit."""
import os

import anthropic
import streamlit as st

from aclaraciones import armar_historia, hay_respuestas, separar_preguntas
from validador import validar_texto

# En modo prueba (tests de Playwright) se usa el simulador en lugar de la IA real.
if os.environ.get("MODO_PRUEBA") == "1":
    from simulador import generar_con_revision
else:
    from generador import generar_con_revision

st.title("Generador de casos Gherkin")
st.write("Pegá una historia de usuario y obtené escenarios en Gherkin.")

historia = st.text_area("Historia de usuario", height=200)


def ejecutar(texto):
    """Genera a partir del texto y guarda el resultado en la sesión. Devuelve True si salió bien."""
    st.session_state.pop("resultado", None)
    try:
        with st.status("Trabajando...", expanded=True) as estado:
            st.session_state["resultado"] = generar_con_revision(texto, avisar=st.write)
            st.session_state["historia_usada"] = texto
            # Cada ronda de preguntas usa claves nuevas para que los cuadros arranquen vacíos.
            st.session_state["ronda"] = st.session_state.get("ronda", 0) + 1
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


if st.button("Generar"):
    if not historia.strip():
        st.session_state.pop("resultado", None)
        st.error("Pegá una historia de usuario antes de generar.")
    else:
        ejecutar(historia)

# El resultado se guarda en la sesión para que no desaparezca al descargar.
resultado = st.session_state.get("resultado")

if resultado and resultado["tipo"] == "preguntas":
    st.warning("La historia necesita aclaraciones antes de generar escenarios:")
    preguntas = separar_preguntas(resultado["contenido"])
    ronda = st.session_state.get("ronda", 0)

    if preguntas:
        st.write("Respondé las que sepas. Las que dejes vacías se toman como supuestos.")
        respuestas = [
            st.text_input(f"Pregunta {numero}: {pregunta}", key=f"respuesta_{ronda}_{numero}")
            for numero, pregunta in enumerate(preguntas, start=1)
        ]
    else:
        # Si las preguntas no vienen numeradas, se muestran tal cual con un solo cuadro.
        st.markdown(resultado["contenido"])
        preguntas = [resultado["contenido"]]
        respuestas = [st.text_area("Tus respuestas", key=f"respuesta_{ronda}_todas")]

    if st.button("Generar con respuestas"):
        if not hay_respuestas(respuestas):
            st.error("Respondé al menos una pregunta antes de generar.")
        else:
            texto = armar_historia(st.session_state["historia_usada"], preguntas, respuestas)
            if ejecutar(texto):
                st.rerun()  # vuelve a dibujar la pantalla con el nuevo resultado

if resultado and resultado["tipo"] == "feature":
    feature = resultado["contenido"]
    graves = [p for p in resultado["problemas"] if p.get("gravedad") == "alta"]
    menores = [p for p in resultado["problemas"] if p.get("gravedad") != "alta"]
    intentos = len(resultado["historial"])

    st.subheader("Revisión")
    st.caption(f"Intentos usados: {intentos} de 3")
    if not resultado["revisor_ok"]:
        st.warning("El revisor IA no respondió en el formato esperado: la revisión de contenido está incompleta.")
    if graves:
        st.error("Quedaron problemas sin resolver. Revisalos antes de usar el archivo:")
        for p in graves:
            st.markdown(f"- **{p['regla']}**: {p['detalle']}")
    else:
        st.success("Sin problemas graves.")
    if menores:
        with st.expander(f"Sugerencias menores ({len(menores)})"):
            for p in menores:
                st.markdown(f"- **{p['regla']}**: {p['detalle']}")

    st.subheader("Validación automática")
    for regla, errores in validar_texto(feature).items():
        if errores:
            st.error(f"{regla}: " + " | ".join(errores))
        else:
            st.success(f"{regla}: OK")

    if "Aclaraciones:" in st.session_state.get("historia_usada", ""):
        with st.expander("Historia usada (con tus respuestas)"):
            st.text(st.session_state["historia_usada"])

    st.subheader("Escenarios")
    st.code(feature, language="gherkin", wrap_lines=True)
    st.download_button(
        "Descargar .feature",
        data=feature,
        file_name="casos.feature",
        mime="text/plain",
    )

    with st.expander("Historial de intentos"):
        for paso in resultado["historial"]:
            st.markdown(f"**Intento {paso['intento']}**: {len(paso['problemas'])} problema(s)")
            for p in paso["problemas"]:
                st.markdown(f"- {p['regla']} ({p.get('gravedad', '?')}): {p['detalle']}")
