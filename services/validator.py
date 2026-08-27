import re
import unicodedata

from services.rules import REGLAS


def buscar(documentos, tipo):

    for documento in documentos:
        if documento.tipo == tipo:
            return documento

    return None


def quitar_tildes(texto):

    if texto is None:
        return None

    texto = unicodedata.normalize("NFD", str(texto))

    return "".join(
        caracter
        for caracter in texto
        if unicodedata.category(caracter) != "Mn"
    )


def limpiar_nit(valor):

    if valor is None:
        return None

    numeros = re.sub(
        r"[^0-9]",
        "",
        str(valor)
    )

    return numeros if numeros else None


def limpiar_razon_social(valor):

    if valor is None:
        return None

    valor = quitar_tildes(valor).upper()

    # Eliminar expresiones que pueden variar entre documentos
    valor = valor.replace(
        "SOCIEDAD POR ACCIONES SIMPLIFICADA",
        ""
    )

    valor = re.sub(
        r"S\.?\s*A\.?\s*S\.?",
        "",
        valor
    )

    # Eliminar puntuación
    valor = re.sub(
        r"[^A-Z0-9 ]",
        " ",
        valor
    )

    valor = re.sub(
        r"\s+",
        " ",
        valor
    ).strip()

    return valor


def limpiar_direccion(valor):

    if valor is None:
        return None

    valor = quitar_tildes(valor).upper().strip()

    # Eliminar ubicación adicional
    for texto in [
        "MEDELLIN",
        "COLOMBIA",
        "ANTIOQUIA"
    ]:
        valor = valor.replace(texto, "")

    # Normalizar tipos de vía
    reemplazos = [
        ("CARRERA", "CR"),
        ("CRA.", "CR"),
        ("CRA", "CR"),
        ("CALLE", "CL"),
        ("CLL.", "CL"),
        ("CLL", "CL"),
        ("AVENIDA", "AV"),
        ("AV.", "AV"),
        ("DIAGONAL", "DG"),
        ("TRANSVERSAL", "TV")
    ]

    for original, nuevo in reemplazos:
        valor = valor.replace(original, nuevo)

    # Eliminar número, signos y puntuación
    valor = valor.replace("N°", " ")
    valor = valor.replace("NO.", " ")
    valor = valor.replace("#", " ")

    valor = re.sub(
        r"[^A-Z0-9]",
        "",
        valor
    )

    return valor


def limpiar_numero(valor):

    if valor is None:
        return None

    valor = str(valor).strip().upper()

    if not valor:
        return None

    # Eliminar símbolos monetarios y unidades
    for texto in [
        "USD",
        "US$",
        "COP",
        "$",
        "KG",
        "KGS",
        "KILOGRAMOS",
        "LB"
    ]:
        valor = valor.replace(texto, "")

    valor = valor.strip()

    # Eliminar espacios
    valor = valor.replace(" ", "")

    # Formato: 28,350.00
    if "," in valor and "." in valor:

        ultima_coma = valor.rfind(",")
        ultimo_punto = valor.rfind(".")

        if ultimo_punto > ultima_coma:
            valor = valor.replace(",", "")
        else:
            valor = valor.replace(".", "")
            valor = valor.replace(",", ".")

    # Formato con coma decimal
    elif "," in valor:

        partes = valor.split(",")

        if len(partes[-1]) == 2:
            valor = valor.replace(",", ".")
        else:
            valor = valor.replace(",", "")

    try:
        return round(float(valor), 2)

    except ValueError:
        return None


def comparar_nit(valor1, valor2):

    nit1 = limpiar_nit(valor1)
    nit2 = limpiar_nit(valor2)

    if not nit1 or not nit2:
        return False

    # Exactamente iguales
    if nit1 == nit2:
        return True

    # Un documento puede incluir el dígito de verificación
    if len(nit1) == len(nit2) + 1:
        return nit1[:-1] == nit2

    if len(nit2) == len(nit1) + 1:
        return nit2[:-1] == nit1

    return False


def comparar_razon_social(valor1, valor2):

    razon1 = limpiar_razon_social(valor1)
    razon2 = limpiar_razon_social(valor2)

    if not razon1 or not razon2:
        return False

    if razon1 == razon2:
        return True

    if razon1 in razon2:
        return True

    if razon2 in razon1:
        return True

    return False


def comparar_direccion(valor1, valor2):

    direccion1 = limpiar_direccion(valor1)
    direccion2 = limpiar_direccion(valor2)

    if not direccion1 or not direccion2:
        return False

    return direccion1 == direccion2


def comparar_numero(valor1, valor2):

    numero1 = limpiar_numero(valor1)
    numero2 = limpiar_numero(valor2)

    if numero1 is None or numero2 is None:
        return False

    return abs(numero1 - numero2) < 0.01


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

            nombre = regla["nombre"].upper()

            if "NIT" in nombre:

                coincide = comparar_nit(
                    valor1,
                    valor2
                )

            elif (
                "RAZON" in nombre
                or "RAZÓN" in nombre
                or "SOCIAL" in nombre
            ):

                coincide = comparar_razon_social(
                    valor1,
                    valor2
                )

            elif "DIRECCION" in nombre or "DIRECCIÓN" in nombre:

                coincide = comparar_direccion(
                    valor1,
                    valor2
                )

            elif (
                "VALOR" in nombre
                or "PESO" in nombre
            ):

                coincide = comparar_numero(
                    valor1,
                    valor2
                )

            else:

                coincide = (
                    str(valor1).strip().upper()
                    ==
                    str(valor2).strip().upper()
                )

            estado = "OK" if coincide else "ERROR"

        resultados.append({

            "validacion": regla["nombre"],
            "estado": estado,
            "valor_1": valor1,
            "valor_2": valor2

        })

    return resultados
