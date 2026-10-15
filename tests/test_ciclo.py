"""Tests del ciclo generar → validar → revisar → corregir, con funciones falsas (sin IA)."""
from generador import MAX_CORRECCIONES, ciclo_de_revision

GRAVE = {"regla": "B12", "gravedad": "alta", "detalle": "Paso ambiguo"}
MENOR = {"regla": "B15", "gravedad": "baja", "detalle": "Título mejorable"}


def respuesta(contenido, tipo="reporte"):
    return {"tipo": tipo, "contenido": contenido}


def correr(revisiones, corregir_fn=None, generar_fn=None):
    """Corre el ciclo con un revisor que devuelve, en cada intento, la lista indicada."""
    pendientes = list(revisiones)
    llamadas = {"corregir": 0}

    def corregir(entrada, salida, graves):
        llamadas["corregir"] += 1
        return respuesta(f"versión {llamadas['corregir'] + 1}")

    resultado = ciclo_de_revision(
        "entrada",
        generar_fn=generar_fn or (lambda e: respuesta("versión 1")),
        corregir_fn=corregir_fn or corregir,
        revisar_fn=lambda e, s: pendientes.pop(0),
        validar_fn=lambda s, e: {"B01": []},
        tipo="reporte",
    )
    return resultado, llamadas["corregir"]


def test_sin_problemas_no_corrige():
    resultado, correcciones = correr([[]])
    assert correcciones == 0
    assert resultado["contenido"] == "versión 1"
    assert len(resultado["historial"]) == 1


def test_los_problemas_menores_no_disparan_correcciones():
    resultado, correcciones = correr([[MENOR]])
    assert correcciones == 0
    assert resultado["problemas"] == [MENOR]


def test_corrige_hasta_que_no_quedan_graves():
    resultado, correcciones = correr([[GRAVE], []])
    assert correcciones == 1
    assert resultado["contenido"] == "versión 2"


def test_no_supera_el_maximo_de_correcciones():
    resultado, correcciones = correr([[GRAVE]] * (MAX_CORRECCIONES + 1))
    assert correcciones == MAX_CORRECCIONES
    assert len(resultado["historial"]) == MAX_CORRECCIONES + 1
    assert resultado["problemas"] == [GRAVE]  # se entregan los problemas que quedaron


def test_si_al_corregir_devuelve_preguntas_se_queda_con_la_ultima_version():
    resultado, _ = correr([[GRAVE]], corregir_fn=lambda e, s, g: respuesta("1. ¿?", "preguntas"))
    assert resultado["tipo"] == "reporte"
    assert resultado["contenido"] == "versión 1"


def test_si_genera_preguntas_las_devuelve_sin_revisar():
    resultado, _ = correr([], generar_fn=lambda e: respuesta("1. ¿Qué pasa?", "preguntas"))
    assert resultado == {"tipo": "preguntas", "contenido": "1. ¿Qué pasa?"}


def test_el_validador_recibe_la_entrada():
    # B08 compara el reporte con lo que contó el QA: el ciclo tiene que pasarle la entrada.
    recibidas = []
    ciclo_de_revision(
        "lo que contó el QA",
        generar_fn=lambda e: respuesta("versión 1"),
        corregir_fn=lambda e, s, g: respuesta("versión 2"),
        revisar_fn=lambda e, s: [],
        validar_fn=lambda s, e: recibidas.append(e) or {"B01": []},
        tipo="reporte",
    )
    assert recibidas == ["lo que contó el QA"]
