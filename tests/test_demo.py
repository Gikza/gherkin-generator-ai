"""Tests del modo demo: busca resultados grabados, sin llamar a la IA."""
import json

import pytest

from demo import SinEjemploGrabado, buscar, cargar_ejemplos, ejemplos_de
from evaluar import ejemplos_para_demo

EJEMPLOS = [
    {"id": "G01", "tipo": "gherkin", "nombre": "Cupón", "entrada": "Como cliente quiero un cupón",
     "historia": "Como cliente quiero un cupón", "resultado": {"tipo": "feature", "contenido": "# language: es"}},
    {"id": "R01", "tipo": "reporte", "nombre": "Bug", "entrada": "Descripción del QA:\nFalla el pago",
     "descripcion": "Falla el pago", "log": "", "resultado": {"tipo": "reporte", "contenido": "**Título:** x"}},
]


def test_encuentra_el_resultado_grabado_aunque_cambien_los_espacios():
    resultado = buscar("  Como cliente   quiero un cupón\n", "gherkin", EJEMPLOS)
    assert resultado["tipo"] == "feature"


def test_no_mezcla_tipos():
    with pytest.raises(SinEjemploGrabado):
        buscar("Como cliente quiero un cupón", "reporte", EJEMPLOS)


def test_una_entrada_propia_da_un_aviso_claro():
    with pytest.raises(SinEjemploGrabado, match="solo funcionan los ejemplos grabados"):
        buscar("Mi propia historia", "gherkin", EJEMPLOS)


def test_filtra_ejemplos_por_tipo():
    assert [e["id"] for e in ejemplos_de("reporte", EJEMPLOS)] == ["R01"]


def test_sin_archivo_de_ejemplos_devuelve_lista_vacia(tmp_path):
    assert cargar_ejemplos(tmp_path / "no_existe.json") == []


def test_carga_ejemplos_desde_archivo(tmp_path):
    ruta = tmp_path / "ejemplos.json"
    ruta.write_text(json.dumps({"ejemplos": EJEMPLOS}), encoding="utf-8")
    assert len(cargar_ejemplos(ruta)) == 2


def test_la_demo_guarda_solo_ejecuciones_aprobadas_y_una_por_caso():
    casos = [{"id": "G01", "tipo": "gherkin", "nombre": "Cupón", "entrada": "historia"},
             {"id": "R01", "tipo": "reporte", "nombre": "Bug", "descripcion": "falla", "log": "500"}]
    resultado = {"tipo": "feature", "contenido": "x"}
    ejecuciones = [
        {"caso": "G01", "aprobado": True, "resultado": resultado},
        {"caso": "G01", "aprobado": True, "resultado": {"tipo": "feature", "contenido": "otra"}},
        {"caso": "R01", "aprobado": False, "resultado": resultado},
    ]
    ejemplos = ejemplos_para_demo(casos, ejecuciones, "modelo-x")["ejemplos"]
    assert [e["id"] for e in ejemplos] == ["G01"]
    assert ejemplos[0]["resultado"]["contenido"] == "x"
    assert ejemplos[0]["historia"] == "historia"
