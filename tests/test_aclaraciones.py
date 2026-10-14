"""Tests unitarios de aclaraciones: separar preguntas y armar la historia con respuestas."""
from aclaraciones import SIN_RESPUESTA, armar_historia, hay_respuestas, separar_preguntas


def test_separa_preguntas_numeradas_sin_el_numero():
    texto = "1. ¿Quién genera el cupón?\n2. ¿Qué tipo de descuento tiene?"
    assert separar_preguntas(texto) == ["¿Quién genera el cupón?", "¿Qué tipo de descuento tiene?"]


def test_acepta_numeros_con_parentesis_y_de_dos_cifras():
    texto = "9) ¿Hay mensajes de error?\n10. ¿Se notifica al cliente?"
    assert separar_preguntas(texto) == ["¿Hay mensajes de error?", "¿Se notifica al cliente?"]


def test_ignora_lineas_sin_numero():
    texto = "Faltan datos:\n1. ¿Cuál es la vigencia?\n\nGracias."
    assert separar_preguntas(texto) == ["¿Cuál es la vigencia?"]


def test_sin_preguntas_numeradas_devuelve_lista_vacia():
    assert separar_preguntas("¿Cuál es el monto mínimo?") == []


def test_hay_respuestas_ignora_vacias_y_espacios():
    assert hay_respuestas(["", "   "]) is False
    assert hay_respuestas(["", "Un administrador"]) is True


def test_arma_historia_con_preguntas_y_respuestas():
    texto = armar_historia(
        "Generar cupón de descuento",
        ["¿Quién genera el cupón?", "¿Cuál es la vigencia?"],
        ["  Un administrador  ", "30 días"],
    )
    assert texto == (
        "Generar cupón de descuento\n"
        "\n"
        "Aclaraciones:\n"
        "1. ¿Quién genera el cupón?\n"
        "   Respuesta: Un administrador\n"
        "2. ¿Cuál es la vigencia?\n"
        "   Respuesta: 30 días"
    )


def test_marca_las_preguntas_sin_responder():
    texto = armar_historia("Historia", ["¿A?", "¿B?"], ["Sí", ""])
    assert f"Respuesta: {SIN_RESPUESTA}" in texto
    assert "Respuesta: Sí" in texto
