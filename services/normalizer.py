import re


def normalizar_numero(valor):

    if valor is None:
        return None

    valor = str(valor).strip()

    if not valor:
        return None

    valor = valor.upper()

    # Eliminar moneda y unidades
    valor = valor.replace("USD", "")
    valor = valor.replace("US$", "")
    valor = valor.replace("COP", "")
    valor = valor.replace("$", "")
    valor = valor.replace("KG", "")
    valor = valor.replace("KGS", "")
    valor = valor.strip()

    # Eliminar espacios
    valor = valor.replace(" ", "")

    # Caso:
    # 3.284,97
    # 32.834,97
    if "." in valor and "," in valor:

        # Si la coma aparece después del punto,
        # asumimos formato latino:
        # 3.284,97
        if valor.rfind(",") > valor.rfind("."):

            valor = valor.replace(".", "")
            valor = valor.replace(",", ".")

        else:

            # Formato:
            # 3,284.97
            valor = valor.replace(",", "")

    # Caso con únicamente coma:
    # 3284,97
    elif "," in valor:

        partes = valor.split(",")

        if len(partes[-1]) <= 2:

            valor = valor.replace(",", ".")

        else:

            valor = valor.replace(",", "")

    try:

        numero = float(valor)

        return f"{numero:.2f}"

    except Exception:

        return str(valor).upper().strip()


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

    campos_numericos = [

        "valor_factura",
        "valor_fob_usd",
        "valor_cif_usd",
        "peso_bruto",
        "peso_neto"
    ]

    for clave, valor in datos.items():

        clave = mapa.get(
            clave,
            clave
        )

        if clave in campos_numericos:

            valor = normalizar_numero(valor)

        elif isinstance(valor, str):

            valor = valor.strip().upper()

        resultado[clave] = valor

    return resultado
