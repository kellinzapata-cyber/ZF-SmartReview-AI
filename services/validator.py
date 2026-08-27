import re
import unicodedata

from services.rules import REGLAS


def buscar(documentos, tipo):

    for documento in documentos:

        if documento.tipo == tipo:
            return documento

    return None


def quitar_tildes(texto):

    texto = unicodedata.normalize(
        "NFD",
        str(texto)
    )

    texto = "".join(
        caracter
        for caracter in texto
        if unicodedata.category(caracter) != "Mn"
    )

    return texto


def limpiar_general(valor):

    if valor is None:
        return None

    valor = str(valor).strip()

    if not valor:
        return None

    valor = quitar_tildes(valor)

    valor = valor.upper()

    valor = valor.replace("N°", "")
    valor = valor.replace("NO.", "")
    valor = valor.replace("NUMERO", "")

    valor = re.sub(
        r"[^A-Z0-9]",
        "",
        valor
    )

    return valor


def limpiar_nit(valor):

    if valor is None:
        return None

    valor = str(valor).strip()

    if not valor:
        return None

    # Conservamos únicamente números
    numeros = re.sub(
        r"[^0-9]",
        "",
        valor
    )

    # Si tiene 10 dígitos, normalmente
    # el último puede ser el dígito de verificación.
    # Para comparar documentos se conserva el número completo.
    return numeros


def limpiar_direccion(valor):

    if valor is None:
        return None

    valor = quitar_tildes(valor).upper()

    # Normalización de palabras
    reemplazos = {

        "CARRERA": "CR",
        "CRA": "CR",
        "CRA.": "CR",

        "CALLE": "CL",
        "CLL": "CL",
        "CL.": "CL",

        "AVENIDA": "AV",
        "AVENIDA ": "AV",

        "DIAGONAL": "DG",
        "TRANSVERSAL": "TV"
    }

    for original, nuevo in reemplazos.items():

        valor = valor.replace(
            original,
            nuevo
        )

    # Eliminar ciudad y país
    lugares = [
        "MEDELLIN",
        "MEDELLIN COLOMBIA",
        "COLOMBIA",
        "ANTIOQUIA"
    ]

    for lugar in lugares:

        valor = valor.replace(
            lugar,
            ""
        )

    # Eliminar símbolos
    valor = valor.replace("N°", "")
    valor = valor.replace("NO.", "")
    valor = valor.replace("#", "")

    # Separar letras y números cuando vienen juntos
    valor = re.sub(
        r"([0-9])([A-Z])",
        r"\1 \2",
        valor
    )

    valor = re.sub(
        r"([A-Z])([0-9])",
        r"\1 \2",
        valor
    )

    # Eliminar puntuación
    valor = re.sub(
        r"[^A-Z0-9]",
        " ",
        valor
    )

    # Eliminar espacios repetidos
    valor = re.sub(
        r"\s+",
        " ",
        valor
    )

    return valor.strip()


def limpiar_razon_social(valor):

    if valor is None:
        return None

    valor = quitar_tildes(valor).upper()

    # Eliminar puntuación
    valor = re.sub(
        r"[^A-Z0-9 ]",
        " ",
        valor
    )

    # Palabras societarias que pueden aparecer
    # con distintas puntuaciones
    valor = valor.replace(
        "SOCIEDAD POR ACCIONES SIMPLIFICADA",
        "SAS"
    )

    valor = valor.replace(
        "S A S",
        "SAS"
    )

    valor = valor.replace(
        "SAS",
        ""
    )

    # Espacios múltiples
    valor = re.sub(
        r"\s+",
        " ",
        valor
    )

    return valor.strip()


def limpiar_numero(valor):

    if valor is None:
        return None

    valor = str(valor).strip()

    if not valor:
        return None

    valor = valor.upper()

    # Eliminar monedas
    valor = valor.replace("USD", "")
    valor = valor.replace("US$", "")
    valor = valor.replace("COP", "")
    valor = valor.replace("$", "")

    # Eliminar espacios
    valor = valor.replace(" ", "")

    # Caso: 3,284.97
    if "," in valor and "." in valor:

        ultima_coma = valor.rfind(",")
        ultimo_punto = valor.rfind(".")

        if ultimo_punto > ultima_coma:

            valor = valor.replace(",", "")

        else:

            valor = valor.replace(".", "")
            valor = valor.replace(",", ".")

    elif "," in valor:

        partes = valor.split(",")

        # 3284,97
        if len(partes[-1]) == 2:

            valor = valor.replace(",", ".")

        # 3,284
        else:

            valor = valor.replace(",", "")

    try:

        return round(
            float(valor),
            2
        )

    except ValueError:

        return None


def comparar_texto(valor1, valor2):

    if valor1 is None or valor2 is None:
        return False

    texto1 = limpiar_general(valor1)
    texto2 = limpiar_general(valor2)

    return texto1 == texto2


def comparar_nit(valor1, valor2):

    nit1 = limpiar_nit(valor1)
    nit2 = limpiar_nit(valor2)

    if not nit1 or not nit2:
        return False

    # Comparación directa
    if nit1 == nit2:
        return True

    # Si uno tiene dígito de verificación y otro no
    if len(nit1) == len(nit2) + 1:

        if nit1[:-1] == nit2:
            return True

    if len(nit2) == len(nit1) + 1:

        if nit2[:-1] == nit1:
            return True

    return False


def comparar_razon_social(valor1, valor2):

    razon1 = limpiar_razon_social(valor1)
    razon2 = limpiar_razon_social(valor2)

    if not razon1 or not razon2:
        return False

    if razon1 == razon2:
        return True

    # Comparación por inclusión.
    # Útil cuando un documento agrega una
    # denominación comercial.
    if razon1 in razon2:
        return True

    if razon2 in razon1:
        return True

    palabras1 = set(razon1.split())
    palabras2 = set(razon2.split())

    if not palabras1 or not palabras2:
        return False

    coincidencias = len(
        palabras1.intersection(palabras2)
    )

    total = max(
        len(palabras1),
        len(palabras2)
    )

    porcentaje = coincidencias / total

    # Se considera coincidencia si al menos
    # el 70% de los términos coincide.
    return porcentaje >= 0.70


def comparar_direccion(valor1, valor2):

    direccion1 = limpiar_direccion(valor1)
    direccion2 = limpiar_direccion(valor2)

    if not direccion1 or not direccion2:
        return False

    if direccion1 == direccion2:
        return True

    # Comparación eliminando espacios
    sin_espacios1 = direccion1.replace(" ", "")
    sin_espacios2 = direccion2.replace(" ", "")

    if sin_espacios1 == sin_espacios2:
        return True

    return False


def comparar_numero(valor1, valor2):

    numero1 = limpiar_numero(valor1)
    numero2 = limpiar_numero(valor2)

    if numero1 is None or numero2 is None:
        return False

    # Tolerancia mínima por posibles decimales
    return abs(numero1 - numero2) < 0.01


def comparar_según_validacion(
    nombre,
    valor1,
    valor2
):

    nombre = nombre.upper()

    if "NIT" in nombre:

        return comparar_nit(
            valor1,
            valor2
        )

    if (
        "RAZ" in nombre
        or "SOCIAL" in nombre
    ):

        return comparar_razon_social(
            valor1,
            valor2
        )

    if "DIRECCI" in nombre:

        return comparar_direccion(
            valor1,
            valor2
        )

    if (
        "VALOR" in nombre
        or "PESO" in nombre
        or "FACTURA" in nombre
    ):

        return comparar_numero(
            valor1,
            valor2
        )

    return comparar_texto(
        valor1,
        valor2
    )


def ejecutar_validaciones(documentos):

    resultados = []

    for regla in REGLAS:

        doc1 = buscar(
            documentos,
            regla["documentos"][0]
        )

        doc2 = buscar(
            documentos,
            regla["documentos"][1]
        )

        if not doc1 or not doc2:

            resultados.append({
                "validacion": regla["nombre"],
                "estado": "NO APLICA",
                "valor_1": None,
                "valor_2": None
            })

            continue

        valor1 = doc1.datos.get(
            regla["campo_doc1"]
        )

        valor2 = doc2.datos.get(
            regla["campo_doc2"]
        )

        if valor1 is None or valor2 is None:

            estado = "SIN INFORMACIÓN"

        else:

            coincide = comparar_según_validacion(
                regla["nombre"],
                valor1,
                valor2
            )

            if coincide:

                estado = "OK"

            else:

                estado = "ERROR"

        resultados.append({

            "validacion": regla["nombre"],
            "estado": estado,
            "valor_1": valor1,
            "valor_2": valor2

        })

    return resultados
