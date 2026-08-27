import re
import unicodedata
from services.rules import REGLAS


def buscar(documentos, tipo):

    for doc in documentos:

        if doc.tipo == tipo:
            return doc

    return None


def quitar_tildes(texto):

    texto = unicodedata.normalize(
        "NFD",
        texto
    )

    texto = "".join(
        c for c in texto
        if unicodedata.category(c) != "Mn"
    )

    return texto


def normalizar_texto_comparacion(valor):

    if valor is None:
        return None

    valor = str(valor).upper().strip()

    valor = quitar_tildes(valor)

    # Eliminar puntuación
    valor = valor.replace(".", " ")
    valor = valor.replace(",", " ")
    valor = valor.replace(";", " ")
    valor = valor.replace(":", " ")

    # Normalizar símbolos
    valor = valor.replace("#", " ")
    valor = valor.replace("°", " ")
    valor = valor.replace("º", " ")

    # Razones sociales
    valor = valor.replace("S.A.S.", " SAS ")
    valor = valor.replace("S.A.S", " SAS ")
    valor = valor.replace("SAS.", " SAS ")

    # Direcciones
    valor = valor.replace("CARRERA", "CR")
    valor = valor.replace("CRA", "CR")
    valor = valor.replace("CALLE", "CL")
    valor = valor.replace("AVENIDA", "AV")

    # Eliminar palabras geográficas para comparar direcciones
    valor = valor.replace("MEDELLIN", " ")
    valor = valor.replace("COLOMBIA", " ")

    # Separadores
    valor = valor.replace("-", " ")

    # Espacios múltiples
    valor = re.sub(
        r"\s+",
        " ",
        valor
    )

    return valor.strip()


def normalizar_direccion(valor):

    if valor is None:
        return None

    valor = normalizar_texto_comparacion(valor)

    # Eliminar espacios para comparar estructura
    valor = valor.replace(" ", "")

    return valor


def normalizar_nit(valor):

    if valor is None:
        return None

    valor = str(valor)

    # Conservar solamente números
    numeros = re.sub(
        r"[^0-9]",
        "",
        valor
    )

    # Si el documento tiene NIT + dígito de verificación
    # Ejemplo:
    # 890.916.575-4
    #
    # Se elimina el último número porque es el DV

    if "-" in valor:

        partes = re.findall(
            r"\d+",
            valor
        )

        if len(partes) >= 2:

            return "".join(partes[:-1])

    return numeros


def normalizar_valor(valor):

    if valor is None:
        return None

    if isinstance(valor, (int, float)):

        return round(
            float(valor),
            2
        )

    valor = str(valor).upper()

    valor = valor.replace("USD", "")
    valor = valor.replace("COP", "")
    valor = valor.replace("US$", "")
    valor = valor.replace("$", "")
    valor = valor.strip()

    valor = valor.replace(" ", "")

    # Formato 3.496,49
    if "." in valor and "," in valor:

        if valor.rfind(",") > valor.rfind("."):

            valor = valor.replace(".", "")
            valor = valor.replace(",", ".")

        else:

            valor = valor.replace(",", "")

    elif "," in valor:

        valor = valor.replace(",", ".")

    try:

        return round(
            float(valor),
            2
        )

    except ValueError:

        return None


def comparar_textos(valor1, valor2):

    valor1 = normalizar_texto_comparacion(valor1)
    valor2 = normalizar_texto_comparacion(valor2)

    if not valor1 or not valor2:
        return False

    if valor1 == valor2:
        return True

    # Permite coincidencia cuando uno contiene al otro
    if valor1 in valor2:
        return True

    if valor2 in valor1:
        return True

    return False


def comparar_direcciones(valor1, valor2):

    valor1 = normalizar_direccion(valor1)
    valor2 = normalizar_direccion(valor2)

    if not valor1 or not valor2:
        return False

    if valor1 == valor2:
        return True

    if valor1 in valor2:
        return True

    if valor2 in valor1:
        return True

    return False


def comparar_nit(valor1, valor2):

    valor1 = normalizar_nit(valor1)
    valor2 = normalizar_nit(valor2)

    if not valor1 or not valor2:
        return False

    return valor1 == valor2


def comparar_valores(valor1, valor2):

    valor1 = normalizar_valor(valor1)
    valor2 = normalizar_valor(valor2)

    if valor1 is None or valor2 is None:
        return False

    return abs(valor1 - valor2) < 0.01


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
                "valor_1": "",
                "valor_2": ""

            })

            continue

        campo1 = regla["campo_doc1"]
        campo2 = regla["campo_doc2"]

        valor1 = doc1.datos.get(campo1)
        valor2 = doc2.datos.get(campo2)

        if valor1 is None or valor2 is None:

            estado = "SIN INFORMACIÓN"

        else:

            nombre_regla = regla["nombre"].upper()

            # NIT
            if "NIT" in nombre_regla:

                coincide = comparar_nit(
                    valor1,
                    valor2
                )

            # DIRECCIÓN
            elif "DIRECCIÓN" in nombre_regla or "DIRECCION" in nombre_regla:

                coincide = comparar_direcciones(
                    valor1,
                    valor2
                )

            # VALORES
            elif (
                "VALOR" in nombre_regla
                or "FACTURA" in nombre_regla
                or "PRECIO" in nombre_regla
            ):

                coincide = comparar_valores(
                    valor1,
                    valor2
                )

            # TEXTO GENERAL
            else:

                coincide = comparar_textos(
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
