import re
import unicodedata

from services.rules import REGLAS


def buscar(documentos, tipo):

    for doc in documentos:
        if doc.tipo == tipo:
            return doc

    return None


# ==========================================================
# QUITAR TILDES
# ==========================================================

def quitar_tildes(texto):

    texto = unicodedata.normalize("NFD", texto)

    return "".join(
        caracter
        for caracter in texto
        if unicodedata.category(caracter) != "Mn"
    )


# ==========================================================
# NORMALIZACIÓN GENERAL
# ==========================================================

def limpiar_texto(valor):

    if valor is None:
        return None

    valor = str(valor).strip().upper()

    if valor == "":
        return None

    valor = quitar_tildes(valor)

    # Razón social
    valor = valor.replace("S.A.S.", "SAS")
    valor = valor.replace("S.A.S", "SAS")
    valor = valor.replace("SAS.", "SAS")

    valor = valor.replace("S.A.", "SA")
    valor = valor.replace("S.A", "SA")

    # Direcciones
    valor = valor.replace("CARRERA", "CR")
    valor = valor.replace("CRA.", "CR")
    valor = valor.replace("CRA", "CR")

    valor = valor.replace("CALLE", "CL")
    valor = valor.replace("CL.", "CL")

    valor = valor.replace("AVENIDA", "AV")
    valor = valor.replace("AV.", "AV")

    # Símbolos comunes
    valor = valor.replace("N°", " ")
    valor = valor.replace("NO.", " ")
    valor = valor.replace("NO ", " ")
    valor = valor.replace("#", " ")

    # Ubicación adicional
    valor = valor.replace("MEDELLIN", "")
    valor = valor.replace("COLOMBIA", "")

    # Eliminar puntuación
    valor = re.sub(r"[.,;:]", " ", valor)

    # Guiones como separadores
    valor = valor.replace("-", " ")

    # Separar números y letras
    valor = re.sub(r"(\d)([A-Z])", r"\1 \2", valor)
    valor = re.sub(r"([A-Z])(\d)", r"\1 \2", valor)

    # Espacios múltiples
    valor = re.sub(r"\s+", " ", valor)

    return valor.strip()


# ==========================================================
# NIT
# ==========================================================

def limpiar_nit(valor):

    if valor is None:
        return None

    valor = str(valor).strip()

    if valor == "":
        return None

    # Si viene con dígito de verificación separado por guion
    # Ejemplo: 890.916.575-4
    if "-" in valor:

        valor = valor.split("-")[0]

    # Dejar solamente números
    valor = re.sub(r"[^0-9]", "", valor)

    return valor


def comparar_nit(valor1, valor2):

    nit1 = limpiar_nit(valor1)
    nit2 = limpiar_nit(valor2)

    if not nit1 or not nit2:
        return False

    return nit1 == nit2


# ==========================================================
# RAZÓN SOCIAL
# ==========================================================

def normalizar_razon_social(valor):

    if valor is None:
        return None

    valor = limpiar_texto(valor)

    if not valor:
        return None

    # Eliminar espacios para comparación adicional
    valor = re.sub(r"\s+", " ", valor)

    return valor


def comparar_razon_social(valor1, valor2):

    razon1 = normalizar_razon_social(valor1)
    razon2 = normalizar_razon_social(valor2)

    if not razon1 or not razon2:
        return False

    # Coincidencia exacta
    if razon1 == razon2:
        return True

    # Coincidencia parcial significativa
    if razon1 in razon2:
        return True

    if razon2 in razon1:
        return True

    return False


# ==========================================================
# DIRECCIONES
# ==========================================================

def normalizar_direccion(valor):

    if valor is None:
        return None

    valor = limpiar_texto(valor)

    if not valor:
        return None

    # Para direcciones eliminamos espacios completamente
    # Ejemplo:
    # CR 43 A 25 A 45
    # CR43A25A45
    valor = valor.replace(" ", "")

    return valor


def comparar_direccion(valor1, valor2):

    direccion1 = normalizar_direccion(valor1)
    direccion2 = normalizar_direccion(valor2)

    if not direccion1 or not direccion2:
        return False

    return direccion1 == direccion2


# ==========================================================
# COMPARACIÓN GENERAL
# ==========================================================

def comparar_valores(nombre_validacion, valor1, valor2):

    if valor1 is None or valor2 is None:
        return False

    nombre = nombre_validacion.upper()

    # NIT
    if "NIT" in nombre:

        return comparar_nit(
            valor1,
            valor2
        )

    # Razón social
    if "RAZON SOCIAL" in nombre or "RAZÓN SOCIAL" in nombre:

        return comparar_razon_social(
            valor1,
            valor2
        )

    # Dirección
    if "DIRECCION" in nombre or "DIRECCIÓN" in nombre:

        return comparar_direccion(
            valor1,
            valor2
        )

    # Comparación normal para otros campos
    valor1_normalizado = limpiar_texto(valor1)
    valor2_normalizado = limpiar_texto(valor2)

    return valor1_normalizado == valor2_normalizado


# ==========================================================
# EJECUTAR VALIDACIONES
# ==========================================================

def ejecutar_validaciones(documentos):

    resultados = []

    for regla in REGLAS:

        tipo_doc1 = regla["documentos"][0]
        tipo_doc2 = regla["documentos"][1]

        doc1 = buscar(
            documentos,
            tipo_doc1
        )

        doc2 = buscar(
            documentos,
            tipo_doc2
        )

        # Verificar que existan los documentos
        if not doc1 or not doc2:

            resultados.append({

                "validacion": regla["nombre"],
                "estado": "NO APLICA",
                "valor_1": None,
                "valor_2": None

            })

            continue

        # Obtener valores
        valor1 = doc1.datos.get(
            regla["campo_doc1"]
        )

        valor2 = doc2.datos.get(
            regla["campo_doc2"]
        )

        # Verificar información disponible
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
