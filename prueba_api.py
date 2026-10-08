"""Prueba mínima: verifica que la clave de la API y el modelo funcionan."""
import os

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()  # lee las variables del archivo .env

client = Anthropic()  # usa ANTHROPIC_API_KEY automáticamente
modelo = os.environ["CLAUDE_MODEL"]

respuesta = client.messages.create(
    model=modelo,
    max_tokens=2000,
    messages=[
        {
            "role": "user",
            "content": "Escribí un único escenario en Gherkin, en español, "
                       "para un login exitoso.",
        }
    ],
)

# La respuesta puede traer varios bloques (por ejemplo, el razonamiento
# del modelo antes del texto). Nos quedamos solo con los bloques de texto.
texto = "".join(
    bloque.text for bloque in respuesta.content if bloque.type == "text"
)
print(texto)
