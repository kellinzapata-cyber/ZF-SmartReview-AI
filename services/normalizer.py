import re


def normalizar_numero(valor):

    if valor is None:
        return None

    valor = str(valor).strip()

    if valor == "":
        return None

    # Eliminar espacios
    valor = valor.replace(" ", "")

    # Eliminar separadores de miles
    valor = valor.replace(",", "")

    try:
        numero = float(valor)
        return f"{numero:.2f}"
    except:
        return valor.upper()


def normalizar(datos):

    mapa = {

        "NIT": "nit",
        "Nit": "nit",
        "numero_identificacion": "nit",

        "Razón Social": "razon_social",
        "Razon Social": "razon_social",
        "empresa": "razon_social",

        "Incoterm": "incoterm",

        "Valor Factura": "valor_factura",

        "Peso Bruto": "peso_bruto",

        "Peso Neto": "peso_neto",

        "Usuario Zona Franca": "usuario_zona_franca",

        "Destinatario": "destinatario"
    }

    resultado = {}

    for clave, valor in datos.items():

        clave = mapa.get(clave, clave)

        # Campos numéricos
        if clave in [
            "valor_factura",
            "peso_bruto",
            "peso_neto"
        ]:
            valor = normalizar_numero(valor)

        # Campos de texto
        elif isinstance(valor, str):

            valor = valor.strip().upper()

        resultado[clave] = valor

    return resultado