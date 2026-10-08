# language: es
@regresion
Característica: Registro de paciente en la plataforma
  Como persona que quiere atenderse en la clínica
  Quiero crear una cuenta en la web
  Para poder reservar turnos online

  Antecedentes:
    Dado que el visitante está en el formulario de registro
    Y no inició sesión

  # --- Criterio 7 (camino feliz) ---
  @smoke
  Escenario: Registro exitoso con datos válidos
    Cuando completa el registro con los siguientes datos:
      | campo        | valor               |
      | nombre       | Ana                 |
      | apellido     | Pérez               |
      | dni          | 30123456            |
      | email        | ana.perez@mail.com  |
      | contraseña   | Clave2026           |
      | confirmación | Clave2026           |
    Y acepta los términos y condiciones
    Y envía el formulario
    Entonces la cuenta queda creada en estado "pendiente de activación"
    Y recibe un email de activación en "ana.perez@mail.com"

  Escenario: Activación de la cuenta
    Dado que se registró y su cuenta está "pendiente de activación"
    Cuando abre el enlace de activación recibido por email
    Entonces la cuenta pasa a estado "activa"
    Y puede iniciar sesión

  @negativo
  Escenario: Intentar iniciar sesión sin activar la cuenta
    Dado que se registró y su cuenta está "pendiente de activación"
    Cuando intenta iniciar sesión con sus credenciales
    Entonces se le informa que debe activar la cuenta desde el email recibido

  # --- Criterio 1: campos obligatorios ---
  @negativo
  Esquema del escenario: Campo obligatorio vacío
    Cuando completa el registro con datos válidos excepto "<campo>" vacío
    Y envía el formulario
    Entonces la cuenta no se crea
    Y se indica que "<campo>" es obligatorio

    Ejemplos:
      | campo        |
      | nombre       |
      | apellido     |
      | dni          |
      | email        |
      | contraseña   |
      | confirmación |

  @negativo
  Escenario: Campo obligatorio con solo espacios
    Cuando completa el registro con datos válidos y el nombre "     "
    Y envía el formulario
    Entonces la cuenta no se crea
    Y se indica que "nombre" es obligatorio

  Esquema del escenario: Nombres con caracteres especiales válidos
    Cuando completa el registro con datos válidos y el nombre "<nombre>"
    Y envía el formulario
    Entonces la cuenta queda creada en estado "pendiente de activación"

    Ejemplos:
      | nombre       |
      | María José   |
      | Ñandú        |
      | O'Connor     |

  # --- Criterio 2: email ---
  @negativo
  Esquema del escenario: Email con formato inválido
    Cuando completa el registro con datos válidos y el email "<email>"
    Y envía el formulario
    Entonces la cuenta no se crea
    Y se indica que el email no tiene un formato válido

    Ejemplos:
      | email              |
      | anaperez.mail.com  |
      | ana@               |
      | @mail.com          |
      | ana perez@mail.com |

  @negativo
  Escenario: Email ya registrado
    Dado que existe una cuenta con el email "ana.perez@mail.com"
    Cuando completa el registro con datos válidos y el email "ANA.PEREZ@mail.com"
    Y envía el formulario
    Entonces la cuenta no se crea
    Y se indica que el email ya está registrado

  # --- Criterio 3: DNI ---
  Esquema del escenario: Validación de longitud y formato del DNI
    Cuando completa el registro con datos válidos y el DNI "<dni>"
    Y envía el formulario
    Entonces el registro <resultado>

    Ejemplos:
      | dni       | resultado                          |
      | 1234567   | se acepta                          |
      | 12345678  | se acepta                          |
      | 123456    | se rechaza por longitud inválida   |
      | 123456789 | se rechaza por longitud inválida   |
      | 30.123.456| se rechaza por caracteres inválidos|
      | 3012345A  | se rechaza por caracteres inválidos|

  @negativo
  Escenario: DNI ya registrado
    Dado que existe una cuenta con el DNI "30123456"
    Cuando completa el registro con datos válidos y el DNI "30123456"
    Y envía el formulario
    Entonces la cuenta no se crea
    Y se indica que el DNI ya está registrado

  # --- Criterio 4: contraseña ---
  Esquema del escenario: Reglas de la contraseña
    Cuando completa el registro con datos válidos y la contraseña "<contraseña>" en ambos campos
    Y envía el formulario
    Entonces el registro <resultado>

    Ejemplos:
      | contraseña | resultado                                   |
      | Clave202   | se acepta                                   |
      | Clave20    | se rechaza por tener menos de 8 caracteres  |
      | clave2026  | se rechaza por no tener mayúscula           |
      | ClaveClave | se rechaza por no tener número              |

  # --- Criterio 5: confirmación ---
  @negativo
  Escenario: La confirmación no coincide con la contraseña
    Cuando completa el registro con la contraseña "Clave2026" y la confirmación "Clave2027"
    Y envía el formulario
    Entonces la cuenta no se crea
    Y se indica que las contraseñas no coinciden

  # --- Criterio 6: términos ---
  @negativo
  Escenario: No acepta los términos y condiciones
    Cuando completa el registro con datos válidos
    Pero no acepta los términos y condiciones
    Y envía el formulario
    Entonces la cuenta no se crea
    Y se indica que debe aceptar los términos y condiciones
