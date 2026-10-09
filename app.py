"""Generador de casos Gherkin: interfaz web con Streamlit."""
import os

import anthropic
import streamlit as st

from validador import validar_texto

# En modo prueba (tests de Playwright) se usa el simulador en lugar de la IA real.
if os.environ.get("MODO_PRUEBA") == "1":
    from simulador import generar_con_revision
else:
    from generador import generar_con_revision

st.title("Generador de casos Gherkin")
st.write("Pegá una historia de usuario y obtené escenarios en Gherkin.")

historia = st.text_area("Historia de usuario", height=200)

if st.button("Generar"):
    st.session_state.pop("resultado", None)
    if not historia.strip():
        st.error("Pegá una historia de usuario antes de generar.")
    else:
        try:
            with st.status("Trabajando...", expanded=True) as estado:
                st.session_state["resultado"] = generar_con_revision(historia, avisar=st.write)
                estado.update(label="Listo", state="complete", expanded=False)
        except (anthropic.APITimeoutError, TimeoutError):
            st.error("La IA tardó demasiado en responder. Probá de nuevo en un momento.")
        except anthropic.AuthenticationError:
            st.error("La clave de la API no es válida. Revisá el archivo .env.")
        except anthropic.APIError as error:
            st.error(f"No se pudo generar. Error de la API: {error}")
        except KeyError:
            st.error("Falta CLAUDE_MODEL en el archivo .env.")

# El resultado se guarda en la sesión para que no desaparezca al descargar.
resultado = st.session_state.get("resultado")

if resultado and resultado["tipo"] == "preguntas":
    st.warning("La historia necesita aclaraciones antes de generar escenarios:")
    st.markdown(resultado["contenido"])

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
