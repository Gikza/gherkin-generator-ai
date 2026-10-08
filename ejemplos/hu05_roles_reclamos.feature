# language: es
@regresion
Característica: Permisos por rol en el panel de reclamos
  Como responsable del área de atención al cliente
  Quiero que cada rol tenga permisos distintos en el panel de reclamos
  Para que cada persona solo pueda hacer lo que corresponde a su función

  Antecedentes:
    Dado que existen los usuarios activos:
      | usuario | rol        | equipo |
      | admin1  | Admin      | -      |
      | super1  | Supervisor | Norte  |
      | oper1   | Operador   | Norte  |
      | oper2   | Operador   | Norte  |
      | oper3   | Operador   | Sur    |
    Y existe el reclamo "R-100" del equipo "Norte" asignado a "oper1"
    Y existe el reclamo "R-200" del equipo "Sur" asignado a "oper3"

  # --- Matriz de permisos (criterios 1 a 3 y 6) ---
  Esquema del escenario: Acciones permitidas según el rol
    Dado que "<usuario>" inició sesión
    Cuando intenta <acción>
    Entonces la acción se realiza correctamente

    Ejemplos: Operador
      | usuario | acción                                    |
      | oper1   | ver el reclamo "R-100"                    |
      | oper1   | cambiar el estado de "R-100" a "En curso" |
      | oper1   | agregar un comentario en "R-100"          |

    Ejemplos: Supervisor
      | usuario | acción                                    |
      | super1  | ver el reclamo "R-100"                    |
      | super1  | reasignar "R-100" a "oper2"               |
      | super1  | reabrir "R-100" estando "Resuelto"        |

    Ejemplos: Admin
      | usuario | acción                                    |
      | admin1  | ver el reclamo "R-200"                    |
      | admin1  | crear un usuario con rol "Operador"       |
      | admin1  | cambiar el rol de "oper2" a "Supervisor"  |
      | admin1  | desactivar al usuario "oper2"             |

  @negativo
  Esquema del escenario: Acciones denegadas según el rol
    Dado que "<usuario>" inició sesión
    Cuando intenta <acción>
    Entonces la acción es rechazada con el mensaje "No tenés permisos para realizar esta acción"
    Y no se modifica ningún dato

    Ejemplos: Operador
      | usuario | acción                                     |
      | oper2   | ver el reclamo "R-100"                     |
      | oper2   | cambiar el estado de "R-100" a "En curso"  |
      | oper1   | reasignar "R-100" a "oper2"                |
      | oper1   | reabrir "R-100" estando "Resuelto"         |
      | oper1   | crear un usuario con rol "Operador"        |

    Ejemplos: Supervisor
      | usuario | acción                                     |
      | super1  | ver el reclamo "R-200"                     |
      | super1  | reasignar "R-100" a "oper3"                |
      | super1  | cambiar el rol de "oper1" a "Supervisor"   |
      | super1  | desactivar al usuario "oper1"              |

  # --- Criterio 7: acceso directo por URL ---
  @negativo
  Escenario: Operador intenta entrar a la gestión de usuarios por URL directa
    Dado que "oper1" inició sesión
    Cuando accede directamente a la dirección de la gestión de usuarios
    Entonces ve el mensaje "No tenés permisos para realizar esta acción"
    Y no ve la lista de usuarios

  @negativo
  Escenario: Usuario sin sesión intenta entrar al panel
    Dado que un visitante no inició sesión
    Cuando accede directamente a la dirección del reclamo "R-100"
    Entonces se le solicita iniciar sesión

  # --- Criterio 4: restricciones del admin ---
  @smoke
  Escenario: El admin cambia el rol de un usuario
    Dado que "admin1" inició sesión
    Cuando cambia el rol de "oper2" a "Supervisor"
    Entonces "oper2" tiene el rol "Supervisor"
    Y el cambio queda registrado en la auditoría con usuario, fecha, rol anterior y rol nuevo

  @negativo
  Escenario: El admin no puede desactivarse a sí mismo
    Dado que "admin1" inició sesión
    Cuando intenta desactivar al usuario "admin1"
    Entonces la acción es rechazada
    Y se indica que no puede desactivar su propia cuenta

  @negativo
  Escenario: No se puede quitar el rol al último admin activo
    Dado que existe el usuario activo "admin2" con rol "Admin"
    Y "admin2" inició sesión
    Y "admin1" fue desactivado
    Cuando intenta cambiar su propio rol a "Supervisor"
    Entonces la acción es rechazada
    Y se indica que debe quedar al menos un admin activo

  # --- Criterio 5: usuarios desactivados ---
  @negativo
  Escenario: Un usuario desactivado no puede iniciar sesión
    Dado que el admin desactivó al usuario "oper2"
    Cuando "oper2" intenta iniciar sesión con credenciales válidas
    Entonces el inicio de sesión es rechazado
    Y se indica que la cuenta está desactivada

  Escenario: Desactivar a un operador con reclamos asignados
    Dado que "admin1" inició sesión
    Cuando desactiva al usuario "oper1"
    Entonces el reclamo "R-100" queda sin asignar
    Y el supervisor del equipo "Norte" ve "R-100" como pendiente de asignación

  # --- Cambios de rol con sesión abierta ---
  Escenario: Un cambio de rol se aplica en la siguiente acción
    Dado que "oper2" inició sesión
    Y el admin cambia el rol de "oper2" a "Supervisor"
    Cuando "oper2" intenta reasignar "R-100" a "oper1"
    Entonces la acción se realiza correctamente

  @negativo
  Escenario: Un usuario desactivado con sesión abierta pierde el acceso
    Dado que "oper1" inició sesión
    Y el admin desactiva al usuario "oper1"
    Cuando "oper1" intenta cambiar el estado de "R-100" a "En curso"
    Entonces la sesión se cierra
    Y se indica que la cuenta está desactivada
