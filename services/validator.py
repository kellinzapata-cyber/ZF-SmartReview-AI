import re
import unicodedata
from services.rules import REGLAS


def buscar(documentos, tipo):

    for doc in documentos:
        if doc.tipo == tipo:
            return doc

    return None


def quitar_tildes(texto):

    texto = unicodedata.normalize("NFD", texto)

    return "".join(
        caracter
        for caracter in texto
        if unicodedata.category(caracter) != "Mn"
    )


def limpiar_texto(valor):

    if valor is None:
        return None

    valor = str(valor).strip().upper()

    # Quitar tildes
    valor = quitar_tildes(valor)

    # Normalizar razón social
    valor = valor.replace("S.A.S.", "SAS")
    valor = valor.replace("S.A.S", "SAS")
    valor = valor.replace("SAS.", "SAS")

    valor = valor.replace("S.A.", "SA")
    valor = valor.replace("S.A", "SA")

    # Normalizar tipos de vías
    valor = valor.replace("CARRERA", "CR")
    valor = valor.replace("CRA.", "CR")
    valor = valor.replace("CRA", "CR")

    valor = valor.replace("CALLE", "CL")
    valor = valor.replace("CL.", "CL")

    valor = valor.replace("AVENIDA", "AV")
    valor = valor.replace("AV.", "AV")

    # Normalizar números de dirección
    valor = valor.replace("N°", " ")
    valor = valor.replace("NO.", " ")
    valor = valor.replace("NO ", " ")
    valor = valor.replace("#", " ")

    # Eliminar ubicación adicional
    valor = valor.replace("MEDELLIN", "")
    valor = valor.replace("COLOMBIA", "")

    # Eliminar puntuación
    valor = re.sub(r"[.,;:]", " ", valor)

    # Separar letras y números
    valor = re.sub(r"(\d)([A-Z])", r"\1 \2", valor)
    valor = re.sub(r"([A-Z])(\d)", r"\1 \2", valor)

    # Eliminar guiones como separadores
    valor = valor.replace("-", " ")

    # Quitar espacios múltiples
    valor = re.sub(r"\s+", " ", valor)

    return valor.strip()


def limpiar_nit(valor):

    if valor is None:
        return None

    valor = str(valor).strip()

    # Eliminar todo excepto números
    valor = re.sub(r"[^0-9]", "", valor)

    if not valor:
        return None

    # Si tiene dígito de verificación
    # Un NIT colombiano normalmente tiene 9 dígitos
    # + 1 dígito de verificación

    if len(valor) == 10:
        valor = valor[:9]

    return valor


def normalizar_razon_social(valor):

    if valor is None:
        return None

    valor = limpiar_texto(valor)

    return valor


def normalizar_direccion(valor):

    if valor is None:
        return None

    valor = limpiar_texto(valor)

    return valor


def comparar_razon_social(valor1, valor2):

    valor1 = normalizar_razon_social(valor1)
    valor2 = normalizar_razon_social(valor2)

    if not valor1 or not valor2:
        return False

    # Coincidencia exacta
    if valor1 == valor2:
        return True

    # Permite coincidencia cuando uno contiene al otro.
    # Útil cuando un documento agrega un nombre comercial.
    if valor1 in valor2:
        return True

    if valor2 in valor1:
        return True

    return False


def comparar_direccion(valor1, valor2):

    valor1 = normalizar_direccion(valor1)
    valor2 = normalizar_direccion(valor2)

    if not valor1 or not valor2:
        return False

    # Comparación exacta
    if valor1 == valor2:
        return True

    # Comparación eliminando espacios
    direccion1 = valor1.replace(" ", "")
    direccion2 = valor2.replace(" ", "")

    if direccion1 == direccion2:
        return True

    return False


def comparar_valores(nombre_validacion, valor1, valor2):

    if valor1 is None or valor2 is None:
        return False

    nombre = nombre_validacion.upper()

    # Comparación especial para NIT
    if "NIT" in nombre:

        nit1 = limpiar_nit(valor1)
        nit2 = limpiar_nit(valor2)

        return nit1 == nit2

    # Comparación especial para razón social
    if "RAZON" in nombre or "RAZÓN" in nombre:

        return comparar_razon_social(
            valor1,
            valor2
        )

    # Comparación especial para dirección
    if "DIRECCION" in nombre or "DIRECCIÓN" in nombre:

        return comparar_direccion(
            valor1,
            valor2
        )

    # Comparación general
    valor1_normalizado = limpiar_texto(valor1)
    valor2_normalizado = limpiar_texto(valor2)

    return valor1_normalizado == valor2_normalizado


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

        # No existen los documentos necesarios
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

        # No se pudo extraer alguno de los datos
        if valor1 is None or valor2 is None:

            estado = "SIN INFORMACIÓN"

        else:

            coinciden = comparar_valores(
                regla["nombre"],
                valor1,
                valor2
            )

            if coinciden:
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
