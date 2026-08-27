import re


# =========================================================
# NORMALIZAR NÚMEROS
# =========================================================

def normalizar_numero(valor):

    if valor is None:
        return None

    valor = str(valor).strip()

    if valor == "":
        return None

    # Convertir a mayúsculas
    valor = valor.upper()

    # Eliminar símbolos y palabras relacionadas
    valor = valor.replace("USD", "")
    valor = valor.replace("US$", "")
    valor = valor.replace("COP", "")
    valor = valor.replace("$", "")
    valor = valor.replace("KG", "")
    valor = valor.replace("KGS", "")
    valor = valor.replace("KILOGRAMOS", "")
    valor = valor.replace("KILOGRAMO", "")

    # Eliminar espacios
    valor = valor.replace(" ", "").strip()

    # Conservar únicamente números, puntos, comas y signo negativo
    valor = re.sub(
        r"[^0-9,.\-]",
        "",
        valor
    )

    if valor == "":
        return None

    try:

        tiene_punto = "." in valor
        tiene_coma = "," in valor

        # =================================================
        # CASO 1
        # 28.350,00
        # Formato colombiano/europeo
        # =================================================

        if tiene_punto and tiene_coma:

            if valor.rfind(",") > valor.rfind("."):

                # El punto es separador de miles
                valor = valor.replace(".", "")

                # La coma es decimal
                valor = valor.replace(",", ".")

            else:

                # La coma es separador de miles
                valor = valor.replace(",", "")

        # =================================================
        # CASO 2
        # Solo coma
        # =================================================

        elif tiene_coma:

            partes = valor.split(",")

            # 28,350
            # Puede ser separador de miles
            if (
                len(partes) == 2
                and len(partes[1]) == 3
            ):

                valor = valor.replace(",", "")

            else:

                # 28350,00
                valor = valor.replace(",", ".")

        # =================================================
        # CASO 3
        # Solo punto
        # =================================================

        elif tiene_punto:

            partes = valor.split(".")

            # 28.350
            # Probablemente separador de miles
            if (
                len(partes) == 2
                and len(partes[1]) == 3
            ):

                valor = valor.replace(".", "")

            # Si hay varios puntos
            elif len(partes) > 2:

                ultimo = partes[-1]

                # Si el último grupo tiene 2 decimales
                if len(ultimo) == 2:

                    valor = (
                        "".join(partes[:-1])
                        + "."
                        + ultimo
                    )

                else:

                    valor = valor.replace(".", "")

        numero = float(valor)

        return f"{numero:.2f}"

    except (ValueError, TypeError):

        return str(valor).upper().strip()


# =========================================================
# NORMALIZAR TEXTO
# =========================================================

def normalizar_texto(valor):

    if valor is None:
        return None

    valor = str(valor).strip()

    if valor == "":
        return None

    # Convertir a mayúsculas
    valor = valor.upper()

    # Eliminar espacios múltiples
    valor = re.sub(
        r"\s+",
        " ",
        valor
    )

    return valor.strip()


# =========================================================
# NORMALIZAR NIT
# =========================================================

def normalizar_nit(valor):

    if valor is None:
        return None

    valor = str(valor).strip()

    if valor == "":
        return None

    # Eliminar espacios
    valor = valor.replace(" ", "")

    # IMPORTANTE:
    # No convertir a float.
    # El NIT debe conservarse como texto.

    return valor


# =========================================================
# NORMALIZAR DATOS DEL DOCUMENTO
# =========================================================

def normalizar(datos):

    if not isinstance(datos, dict):
        return datos

    mapa = {

        # NIT
        "NIT": "nit",
        "Nit": "nit",
        "numero_identificacion": "nit",
        "numero_identificación": "nit",

        # Razón social
        "Razón Social": "razon_social",
        "Razon Social": "razon_social",
        "razon social": "razon_social",
        "empresa": "razon_social",

        # Dirección
        "Dirección": "direccion",
        "Direccion": "direccion",

        # Incoterm
        "Incoterm": "incoterm",
        "INCOTERM": "incoterm",

        # Valor factura
        "Valor Factura": "valor_factura",
        "valor factura": "valor_factura",
        "valor_total_factura": "valor_factura",
        "invoice_total": "valor_factura",

        # Pesos
        "Peso Bruto": "peso_bruto",
        "peso bruto": "peso_bruto",
        "gross_weight": "peso_bruto",

        "Peso Neto": "peso_neto",
        "peso neto": "peso_neto",
        "net_weight": "peso_neto",

        # Zona Franca
        "Usuario Zona Franca": "usuario_zona_franca",
        "usuario zona franca": "usuario_zona_franca",

        # Destinatario
        "Destinatario": "destinatario",
        "destinatario": "destinatario",

        # Tipo
        "Tipo Documento": "tipo_documento"
    }


    resultado = {}


    for clave, valor in datos.items():

        # Convertir la clave al nombre estándar
        clave_normalizada = mapa.get(
            clave,
            clave
        )


        # =============================================
        # NIT
        # =============================================

        if clave_normalizada == "nit":

            valor = normalizar_nit(valor)


        # =============================================
        # CAMPOS NUMÉRICOS
        # =============================================

        elif clave_normalizada in [

            "valor_factura",
            "peso_bruto",
            "peso_neto",
            "cantidad_bultos"

        ]:

            valor = normalizar_numero(valor)


        # =============================================
        # CAMPOS DE TEXTO
        # =============================================

        elif isinstance(valor, str):

            valor = normalizar_texto(valor)


        resultado[clave_normalizada] = valor


    return resultado
