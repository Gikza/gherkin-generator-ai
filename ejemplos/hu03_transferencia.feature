# language: es
@regresion
Característica: Transferencia bancaria a otra cuenta
  Como cliente del banco
  Quiero transferir dinero a otra cuenta desde home banking
  Para pagar o enviar dinero sin ir a una sucursal

  Antecedentes:
    Dado que el cliente "Ana Pérez" inició sesión en home banking
    Y su cuenta de origen tiene un saldo de $100.000,00
    Y hoy no realizó otras transferencias

  # --- Criterios 5 y 6: camino feliz ---
  @smoke
  Escenario: Transferencia exitosa por alias
    Cuando inicia una transferencia al alias "carlos.ruiz.banco" por $10.000,00
    Entonces ve un resumen con el titular "Carlos Ruiz", el banco de destino y el monto
    Cuando confirma la transferencia
    Entonces su saldo pasa a ser $90.000,00
    Y obtiene un comprobante con número de operación, fecha, monto y destinatario

  Escenario: Transferencia exitosa por CBU
    Cuando transfiere $5.000,00 al CBU "0170099220000067797370" y confirma
    Entonces su saldo pasa a ser $95.000,00
    Y obtiene un comprobante con número de operación

  Escenario: Cancelar la transferencia en el resumen
    Cuando inicia una transferencia al alias "carlos.ruiz.banco" por $10.000,00
    Y cancela la operación en el resumen
    Entonces no se realiza ninguna transferencia
    Y su saldo sigue siendo $100.000,00

  # --- Criterio 1: destino ---
  @negativo
  Esquema del escenario: Destino inválido
    Cuando inicia una transferencia a "<destino>" por $1.000,00
    Entonces la operación no avanza
    Y se indica "<mensaje>"

    Ejemplos:
      | destino                 | mensaje                              |
      | 017009922000006779737   | El CBU debe tener 22 dígitos         |
      | 01700992200000677973701 | El CBU debe tener 22 dígitos         |
      | 01700992200000677973AB  | El CBU solo admite números           |
      | 0170099220000067797371  | El CBU no es válido                  |
      | alias.que.no.existe     | No se encontró una cuenta con ese alias |
      |                         | Ingresá un CBU o alias de destino    |

  # --- Criterio 7: misma cuenta ---
  @negativo
  Escenario: Transferir a la propia cuenta de origen
    Cuando inicia una transferencia al CBU de su propia cuenta de origen por $1.000,00
    Entonces la operación no avanza
    Y se indica que la cuenta de destino no puede ser la misma que la de origen

  # --- Criterio 2: formato del monto ---
  @negativo
  Esquema del escenario: Monto con formato inválido
    Cuando inicia una transferencia al alias "carlos.ruiz.banco" por "<monto>"
    Entonces la operación no avanza
    Y se indica que el monto no es válido

    Ejemplos:
      | monto   |
      | 0       |
      | 0,00    |
      | -100    |
      | 10,555  |
      | abc     |
      |         |

  Esquema del escenario: Montos válidos en el límite inferior y con decimales
    Cuando transfiere "<monto>" al alias "carlos.ruiz.banco" y confirma
    Entonces la transferencia se realiza por <monto>

    Ejemplos:
      | monto     |
      | $0,01     |
      | $1.234,56 |

  # --- Criterio 3: saldo ---
  Esquema del escenario: Monto respecto del saldo disponible
    Cuando transfiere <monto> al alias "carlos.ruiz.banco" y confirma
    Entonces la transferencia <resultado>

    @positivo
    Ejemplos: Dentro del saldo
      | monto       | resultado                        |
      | $99.999,99  | se realiza                       |
      | $100.000,00 | se realiza y el saldo queda en $0,00 |

    @negativo
    Ejemplos: Supera el saldo
      | monto       | resultado                            |
      | $100.000,01 | se rechaza por saldo insuficiente    |

  # --- Criterio 4: límite diario ---
  Esquema del escenario: Límite diario acumulado de $500.000
    Dado que su cuenta de origen tiene un saldo de $1.000.000,00
    Y hoy ya transfirió $450.000,00
    Cuando transfiere <monto> al alias "carlos.ruiz.banco" y confirma
    Entonces la transferencia <resultado>

    @positivo
    Ejemplos: Llega justo al límite
      | monto      | resultado   |
      | $50.000,00 | se realiza  |

    @negativo
    Ejemplos: Supera el límite
      | monto      | resultado                                   |
      | $50.000,01 | se rechaza por superar el límite diario     |

  Escenario: El límite diario se reinicia al día siguiente
    Dado que su cuenta de origen tiene un saldo de $1.000.000,00
    Y ayer transfirió $500.000,00
    Cuando hoy transfiere $10.000,00 al alias "carlos.ruiz.banco" y confirma
    Entonces la transferencia se realiza

  # --- Robustez ---
  @negativo
  Escenario: Confirmar dos veces la misma transferencia
    Cuando inicia una transferencia al alias "carlos.ruiz.banco" por $10.000,00
    Y confirma la operación dos veces seguidas
    Entonces se realiza una sola transferencia
    Y su saldo pasa a ser $90.000,00
