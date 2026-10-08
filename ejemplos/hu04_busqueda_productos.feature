# language: es
@regresion
Característica: Búsqueda de productos
  Como usuario registrado o invitado
  Quiero buscar productos por nombre, categoría o código
  Para encontrar rápidamente lo que necesito

  Antecedentes:
    Dado que el catálogo tiene 10.000 productos
    Y entre ellos existen los productos:
      | código  | nombre                 | categoría |
      | CAF-001 | Café molido 500 g      | Almacén   |
      | CAF-002 | Cafetera italiana      | Bazar     |
      | TAZ-010 | Taza para café         | Bazar     |

  # --- Búsqueda por campo (criterio 5) ---
  @smoke
  Escenario: Búsqueda exitosa por nombre
    Dado que el usuario es invitado
    Cuando busca "cafetera"
    Entonces ve el producto "Cafetera italiana" en los resultados

  Esquema del escenario: Búsqueda por cada campo permitido
    Dado que el usuario es <tipo_usuario>
    Cuando busca "<texto>"
    Entonces ve el producto "<producto>" en los resultados

    Ejemplos:
      | tipo_usuario | texto   | producto           |
      | registrado   | Café    | Café molido 500 g  |
      | invitado     | Bazar   | Cafetera italiana  |
      | registrado   | TAZ-010 | Taza para café     |

  # --- Mayúsculas y tildes (criterio 6) ---
  Esquema del escenario: La búsqueda no distingue mayúsculas ni tildes
    Cuando busca "<texto>"
    Entonces ve el producto "Café molido 500 g" en los resultados

    Ejemplos:
      | texto |
      | cafe  |
      | CAFÉ  |
      | CaFe  |

  @negativo
  Escenario: Un error de tipeo no encuentra el producto
    Cuando busca "cafetrea"
    Entonces no ve el producto "Cafetera italiana" en los resultados

  # --- Relevancia (criterio 2) ---
  Escenario: Las coincidencias exactas aparecen primero
    Cuando busca "Taza para café"
    Entonces el primer resultado es "Taza para café"
    Y luego aparecen los resultados con coincidencia parcial

  # --- Paginación (criterio 3) ---
  Esquema del escenario: Paginación de 20 resultados por página
    Dado que existen <cantidad> productos que coinciden con "café"
    Cuando busca "café"
    Entonces ve <en_pagina_1> resultados en la primera página
    Y el resultado indica <paginas> páginas en total

    Ejemplos:
      | cantidad | en_pagina_1 | paginas |
      | 1        | 1           | 1       |
      | 20       | 20          | 1       |
      | 21       | 20          | 2       |

  # --- Sin resultados (criterio 7) ---
  @negativo
  Escenario: Búsqueda sin resultados
    Cuando busca "bicicleta"
    Entonces ve el mensaje "No encontramos productos para «bicicleta»"
    Y ve sugerencias de categorías

  # --- Longitud del texto (criterio 8) ---
  Esquema del escenario: Longitud del texto de búsqueda
    Cuando busca un texto de <largo> caracteres
    Entonces la búsqueda <resultado>

    Ejemplos: Longitudes válidas
      | largo | resultado    |
      | 3     | se realiza   |
      | 100   | se realiza   |

    @negativo
    Ejemplos: Longitudes inválidas
      | largo | resultado                                          |
      | 0     | no se realiza y se pide ingresar un texto          |
      | 2     | no se realiza y se indica el mínimo de 3 caracteres |
      | 101   | no se realiza y se indica el máximo de 100 caracteres |

  @negativo
  Escenario: Texto con solo espacios
    Cuando busca "     "
    Entonces la búsqueda no se realiza
    Y se pide ingresar un texto

  @negativo
  Esquema del escenario: Caracteres especiales no rompen la búsqueda
    Cuando busca "<texto>"
    Entonces ve el mensaje de búsqueda sin resultados
    Y no se muestra ningún error del sistema

    Ejemplos:
      | texto                     |
      | ' OR 1=1 --               |
      | <script>alert(1)</script> |
      | %%%                       |

  # --- Tiempo de respuesta (criterio 1) ---
  Escenario: Tiempo de respuesta con el catálogo completo
    Cuando busca "café"
    Entonces los resultados se muestran en 2 segundos o menos
