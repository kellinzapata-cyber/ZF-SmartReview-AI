def clasificar_documento(texto):

    texto = texto.upper()

    reglas = {

        "DUTA": [
            "DOCUMENTO ÚNICO PARA TRÁNSITO ADUANERO",
            "DOCUMENTO UNICO PARA TRANSITO ADUANERO",
            "OPERACIONES DE TRANSPORTE",
            "TRÁNSITO ADUANERO",
            "TRANSITO ADUANERO"
        ],

        "RUT": [
            "FORMULARIO DEL REGISTRO ÚNICO TRIBUTARIO",
            "FORMULARIO DEL REGISTRO UNICO TRIBUTARIO",
            "REGISTRO ÚNICO TRIBUTARIO",
            "REGISTRO UNICO TRIBUTARIO"
        ],

        "FACTURA COMERCIAL": [
            "COMMERCIAL INVOICE",
            "FACTURA COMERCIAL",
            "INVOICE"
        ],

        "BL": [
            "BILL OF LADING",
            "OCEAN BILL OF LADING",
            "MASTER BILL OF LADING",
            "HOUSE BILL OF LADING"
        ],

        "PACKING LIST": [
            "PACKING LIST",
            "LISTA DE EMPAQUE"
        ],

        "CERTIFICADO DE FLETES": [
            "NEGOTIABLE MULTIMODAL TRANSPORTATION ANDEAN DOCUMENT",
            "DOCUMENTO INTERNACIONAL M.T.D.",
            "COMUNIDAD ANDINA",
            "OTM",
            "LOGISTICA TOTAL"
        ],
    }

    for tipo, frases in reglas.items():
        for frase in frases:
            if frase in texto:
                return tipo

    return "DOCUMENTO DESCONOCIDO"