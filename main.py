import os
from pathlib import Path
from dotenv import load_dotenv

from services.pdf_reader import leer_pdf
from services.document_classifier import clasificar_documento
from services.data_extractor import (
    extraer_datos,
    analizar_pdf_con_gemini
)
from services.models import Documento
from services.normalizer import normalizar
from services.validator import ejecutar_validaciones
from services.supabase_service import (
    guardar_documento,
    guardar_validaciones
)


# ============================================================
# VARIABLES DE ENTORNO
# ============================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


# ============================================================
# TIPOS DE DOCUMENTOS VÁLIDOS
# ============================================================

TIPOS_VALIDOS = [
    "RUT",
    "DUTA",
    "FACTURA COMERCIAL",
    "BL",
    "PACKING LIST",
    "CERTIFICADO DE FLETES"
]


# ============================================================
# PROCESAR EXPEDIENTE
# ============================================================

def procesar_expediente(carpeta="documentos_prueba"):

    carpeta = Path(carpeta)

    documentos = []

    print("\n")
    print("=" * 70)
    print("INICIANDO PROCESAMIENTO DEL EXPEDIENTE")
    print("=" * 70)

    # --------------------------------------------------------
    # RECORRER PDFs
    # --------------------------------------------------------

    for archivo in carpeta.glob("*.pdf"):

        print("\n")
        print("=" * 70)
        print("PROCESANDO:", archivo.name)
        print("=" * 70)

        # ----------------------------------------------------
        # 1. EXTRAER TEXTO CON PYMUPDF
        # ----------------------------------------------------

        try:

            texto = leer_pdf(str(archivo))

        except Exception as e:

            print(
                "Error leyendo PDF con PyMuPDF:",
                str(e)
            )

            texto = ""


        print("\nCantidad de caracteres extraídos:")

        print(len(texto))


        print("\nPrimeros 600 caracteres:")

        print("-" * 70)

        print(texto[:600])

        print("-" * 70)


        # ----------------------------------------------------
        # 2. CLASIFICAR DOCUMENTO
        # ----------------------------------------------------

        tipo = clasificar_documento(texto)

        print("\nTipo detectado inicialmente:")

        print(tipo)


        # ----------------------------------------------------
        # 3. SI EL TEXTO NO FUE LEÍDO CORRECTAMENTE
        #    O EL DOCUMENTO ES DESCONOCIDO
        #    USAR GEMINI DIRECTAMENTE CON EL PDF
        # ----------------------------------------------------

        if (
            len(texto.strip()) < 100
            or tipo == "DOCUMENTO DESCONOCIDO"
        ):

            print(
                "\nDocumento no identificado correctamente."
            )

            print(
                "Solicitando clasificación directamente a Gemini..."
            )


            resultado_gemini = analizar_pdf_con_gemini(
                str(archivo),
                "DOCUMENTO DESCONOCIDO"
            )


            print(
                "\nResultado de clasificación Gemini:"
            )

            print(resultado_gemini)


            tipo_gemini = resultado_gemini.get(
                "tipo_documento"
            )


            # Convertir a mayúsculas
            if tipo_gemini:

                tipo_gemini = (
                    str(tipo_gemini)
                    .strip()
                    .upper()
                )


            # ------------------------------------------------
            # VALIDAR TIPO DEVUELTO POR GEMINI
            # ------------------------------------------------

            if tipo_gemini in TIPOS_VALIDOS:

                tipo = tipo_gemini

                print(
                    "\nTipo corregido por Gemini:"
                )

                print(tipo)


            else:

                print(
                    "\nGemini no pudo identificar un tipo válido."
                )

                tipo = "DOCUMENTO DESCONOCIDO"


        # ----------------------------------------------------
        # 4. EXTRAER INFORMACIÓN DEL DOCUMENTO
        # ----------------------------------------------------

        print(
            "\nExtrayendo información..."
        )


        # Si tenemos texto suficiente
        if len(texto.strip()) >= 100:

            datos = extraer_datos(
                tipo,
                texto
            )


        # Si es PDF escaneado o sin texto
        else:

            datos = analizar_pdf_con_gemini(
                str(archivo),
                tipo
            )


        # ----------------------------------------------------
        # 5. VERIFICAR SI GEMINI DEVOLVIÓ ERROR
        # ----------------------------------------------------

        if "error" in datos:

            print(
                "\nERROR EN LA EXTRACCIÓN:"
            )

            print(datos)


        # ----------------------------------------------------
        # 6. NORMALIZAR DATOS
        # ----------------------------------------------------

        print(
            "\nDatos extraídos:"
        )

        print(datos)


        datos = normalizar(datos)


        print(
            "\nDatos normalizados:"
        )

        print(datos)


        # ----------------------------------------------------
        # 7. CREAR OBJETO DOCUMENTO
        # ----------------------------------------------------

        documento = Documento(

            tipo=tipo,

            archivo=archivo.name,

            datos=datos

        )


        documentos.append(documento)


        # ----------------------------------------------------
        # 8. GUARDAR EN SUPABASE
        # ----------------------------------------------------

        try:

            guardar_documento(documento)

            print(
                "\nDocumento guardado en Supabase."
            )

        except Exception as e:

            print(
                "\nERROR GUARDANDO DOCUMENTO EN SUPABASE:"
            )

            print(str(e))


    # ========================================================
    # RESUMEN
    # ========================================================

    print("\n")
    print("=" * 70)
    print("RESUMEN DE DOCUMENTOS")
    print("=" * 70)


    for doc in documentos:

        print(

            doc.tipo,

            "-",

            doc.archivo

        )


    # ========================================================
    # MOSTRAR DOCUMENTOS Y DATOS
    # ========================================================

    print("\n")
    print("=" * 70)
    print("DOCUMENTOS EXTRAÍDOS")
    print("=" * 70)


    for doc in documentos:

        print("\n")

        print(
            "TIPO:",
            doc.tipo
        )

        print(
            "ARCHIVO:",
            doc.archivo
        )

        print(
            "DATOS:"
        )

        print(
            doc.datos
        )


    # ========================================================
    # EJECUTAR VALIDACIONES
    # ========================================================

    print("\n")
    print("=" * 70)
    print("EJECUTANDO VALIDACIONES")
    print("=" * 70)


    resultado = ejecutar_validaciones(
        documentos
    )


    print("\nRESULTADOS:")


    for r in resultado:

        print(r)


    # ========================================================
    # GUARDAR VALIDACIONES
    # ========================================================

    try:

        guardar_validaciones(
            resultado
        )

        print(
            "\nValidaciones guardadas en Supabase."
        )

    except Exception as e:

        print(
            "\nERROR GUARDANDO VALIDACIONES EN SUPABASE:"
        )

        print(
            str(e)
        )


    print("\n")
    print("=" * 70)
    print("PROCESO TERMINADO")
    print("=" * 70)


    return documentos, resultado


# ============================================================
# EJECUCIÓN DIRECTA
# ============================================================

if __name__ == "__main__":

    print(
        "Gemini API cargada:",
        GEMINI_API_KEY is not None
    )

    print(
        "Supabase URL cargada:",
        SUPABASE_URL is not None
    )

    print(
        "Supabase Key cargada:",
        SUPABASE_KEY is not None
    )


    procesar_expediente()
