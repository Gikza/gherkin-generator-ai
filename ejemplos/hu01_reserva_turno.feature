# language: es
@regresion
Característica: Reserva de turno médico online
  Como paciente registrado
  Quiero reservar un turno con un médico desde la web
  Para no tener que llamar por teléfono

  Antecedentes:
    Dado que el paciente "Ana Pérez" inició sesión con credenciales válidas
    Y existen profesionales con agenda disponible

  # --- Criterio 1: filtros ---
  Esquema del escenario: Filtrar turnos por especialidad y profesional
    Cuando filtra por especialidad "<especialidad>" y profesional "<profesional>"
    Entonces solo ve turnos de la especialidad "<especialidad>"
    Y solo ve turnos del profesional "<profesional>" cuando se indicó uno

    Ejemplos:
      | especialidad | profesional      |
      | Cardiología  | Dr. Juan Gómez   |
      | Pediatría    | (cualquiera)     |

  Escenario: Filtro sin turnos disponibles
    Dado que la especialidad "Dermatología" no tiene turnos en los próximos 30 días
    Cuando filtra por especialidad "Dermatología"
    Entonces se informa que no hay turnos disponibles para ese filtro

  # --- Criterio 2: ventana de 30 días ---
  Esquema del escenario: Visibilidad de turnos según la ventana de 30 días
    Dado que existe un turno libre dentro de <dias> días
    Cuando consulta los turnos disponibles
    Entonces el turno <resultado>

    Ejemplos:
      | dias | resultado      |
      | 1    | se muestra     |
      | 30   | se muestra     |
      | 31   | no se muestra  |

  Escenario: No se muestran turnos ya reservados
    Dado que el turno del lunes a las 10:00 con "Dr. Juan Gómez" ya fue reservado
    Cuando consulta la agenda de "Dr. Juan Gómez"
    Entonces ese turno no aparece como disponible

  # --- Criterio 3: confirmación ---
  @smoke
  Escenario: Reserva exitosa de un turno
    Dado que hay un turno libre con "Dr. Juan Gómez" dentro de 5 días
    Cuando reserva ese turno y confirma
    Entonces el turno queda registrado a su nombre
    Y el turno deja de estar disponible para otros pacientes
    Y recibe un email de confirmación con fecha, hora y profesional

  # --- Criterio 4: superposición ---
  @negativo
  Escenario: Intentar reservar dos turnos en el mismo horario
    Dado que ya tiene un turno el martes a las 11:00 con "Dr. Juan Gómez"
    Cuando intenta reservar el martes a las 11:00 con "Dra. Laura Díaz"
    Entonces la reserva es rechazada
    Y se informa que ya tiene un turno en ese horario

  Escenario: Reservar dos turnos en horarios distintos del mismo día
    Dado que ya tiene un turno el martes a las 11:00
    Cuando reserva un turno el martes a las 15:00
    Entonces la reserva se confirma

  # --- Criterio 5: anticipación mínima ---
  Esquema del escenario: Anticipación mínima de 2 horas
    Dado que existe un turno libre que comienza en <anticipacion>
    Cuando intenta reservarlo
    Entonces la reserva <resultado>

    Ejemplos:
      | anticipacion        | resultado        |
      | 3 horas             | se confirma      |
      | 2 horas exactas     | se confirma      |
      | 1 hora y 59 minutos | es rechazada     |
      | 30 minutos          | es rechazada     |

  @negativo
  Escenario: Mensaje al rechazar por falta de anticipación
    Dado que existe un turno libre que comienza en 1 hora
    Cuando intenta reservarlo
    Entonces se informa que los turnos deben reservarse con al menos 2 horas de anticipación

  # --- Criterio 6: concurrencia ---
  @negativo
  Escenario: Dos pacientes reservan el mismo turno al mismo tiempo
    Dado que "Ana Pérez" y "Carlos Ruiz" seleccionaron el mismo turno libre
    Cuando "Carlos Ruiz" confirma la reserva primero
    Y "Ana Pérez" confirma la reserva después
    Entonces el turno queda registrado a nombre de "Carlos Ruiz"
    Y a "Ana Pérez" se le informa que el turno ya no está disponible
    Y "Ana Pérez" no recibe email de confirmación

  # --- Permisos ---
  @negativo
  Escenario: Usuario sin sesión intenta reservar
    Dado que un visitante no inició sesión
    Cuando intenta reservar un turno
    Entonces se le solicita iniciar sesión antes de continuar
