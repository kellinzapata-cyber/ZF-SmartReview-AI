import re
from services.rules import REGLAS


def buscar(documentos, tipo):

    for doc in documentos:
        if doc.tipo == tipo:
            return doc

    return None


def limpiar_texto(valor):

    if valor is None:
        return None

    valor = str(valor).upper().strip()

    # Eliminar caracteres especiales
    valor = valor.replace(".", "")
    valor = valor.replace(",", "")
    valor = valor.replace(";", "")

    # Monedas
    valor = valor.replace("USD", "")
    valor = valor.replace("US$", "")
    valor = valor.replace("$", "")
    valor = valor.replace("COP", "")

    # Razón social
    valor = valor.replace("S.A.S.", "SAS")
    valor = valor.replace("S.A.S", "SAS")
    valor = valor.replace("SAS.", "SAS")

    # Direcciones
    valor = valor.replace("CALLE", "CL")
    valor = valor.replace("CARRERA", "CR")
    valor = valor.replace("AVENIDA", "AV")
    valor = valor.replace("AV.", "AV")
    valor = valor.replace("#", " ")
    valor = valor.replace("-", " ")

    # Eliminar ciudad y país
    valor = valor.replace("MEDELLÍN", "")
    valor = valor.replace("MEDELLIN", "")
    valor = valor.replace("COLOMBIA", "")

    # Quitar espacios múltiples
    valor = re.sub(r"\s+", " ", valor)

    return valor.strip()


def ejecutar_validaciones(documentos):

    resultados = []

    for regla in REGLAS:

        doc1 = buscar(documentos, regla["documentos"][0])
        doc2 = buscar(documentos, regla["documentos"][1])

        if not doc1 or not doc2:

            resultados.append({
                "validacion": regla["nombre"],
                "estado": "NO APLICA",
                "valor_1": "",
                "valor_2": ""
            })

            continue

        valor1 = doc1.datos.get(regla["campo_doc1"])
        valor2 = doc2.datos.get(regla["campo_doc2"])

        if valor1 is None or valor2 is None:

            estado = "SIN INFORMACIÓN"

        else:

            valor1_normalizado = limpiar_texto(valor1)
            valor2_normalizado = limpiar_texto(valor2)

            if valor1_normalizado == valor2_normalizado:
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