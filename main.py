import os
from dotenv import load_dotenv
from pathlib import Path


load_dotenv()


GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

SUPABASE_URL = os.getenv(
    "SUPABASE_URL"
)

SUPABASE_KEY = os.getenv(
    "SUPABASE_KEY"
)


from services.pdf_reader import leer_pdf

from services.document_classifier import (
    clasificar_documento
)

from services.data_extractor import (
    extraer_datos,
    analizar_pdf_con_gemini
)

from services.models import Documento

from services.normalizer import (
    normalizar
)

from services.validator import (
    ejecutar_validaciones
)

from services.supabase_service import (
    guardar_documento,
    guardar_validaciones
)


def procesar_expediente(carpeta="documentos_prueba"):

    carpeta = Path(carpeta)

    documentos = []

    for archivo in carpeta.glob("*.pdf"):

        print("\n" + "=" * 80)

        print(
            "Procesando:",
            archivo.name
        )

        # ==============================
        # LEER TEXTO DEL PDF
        # ==============================

        texto = leer_pdf(
            str(archivo)
        )

        print(
            "\nCantidad de caracteres extraídos:",
            len(texto)
        )

        print(
            "\nPrimeros 600 caracteres:"
        )

        print(
            texto[:600]
        )

        print(
            "-" * 80
        )


        # ==============================
        # CLASIFICAR DOCUMENTO
        # ==============================

        tipo = clasificar_documento(
            texto
        )

        print(
            f"Tipo detectado: {tipo}"
        )


        # ==============================
        # EXTRAER DATOS
        # ==============================

        # Si el PDF tiene poco texto,
        # probablemente sea escaneado

        if len(texto.strip()) < 200:

            print(
                "\nPDF con poco texto."
            )

            print(
                "Analizando PDF directamente con Gemini..."
            )

            datos = analizar_pdf_con_gemini(
                str(archivo),
                tipo
            )

        else:

            print(
                "\nAnalizando texto con Gemini..."
            )

            datos = extraer_datos(
                tipo,
                texto
            )


        print(
            "\nDatos extraídos:"
        )

        print(
            datos
        )


        # ==============================
        # NORMALIZAR DATOS
        # ==============================

        if "error" not in datos:

            datos = normalizar(
                datos
            )


        print(
            "\nDatos normalizados:"
        )

        print(
            datos
        )


        # ==============================
        # CREAR DOCUMENTO
        # ==============================

        documento = Documento(

            tipo=tipo,

            archivo=archivo.name,

            datos=datos

        )


        documentos.append(
            documento
        )


        # ==============================
        # GUARDAR DOCUMENTO
        # ==============================

        try:

            guardar_documento(
                documento
            )

            print(
                "Documento guardado en Supabase."
            )

        except Exception as e:

            print(
                "Error guardando documento:"
            )

            print(
                str(e)
            )


    # ==============================
    # RESUMEN
    # ==============================

    print(
        "\n" + "=" * 80
    )

    print(
        "RESUMEN DE DOCUMENTOS"
    )

    print(
        "=" * 80
    )

    for doc in documentos:

        print(
            f"{doc.tipo} - {doc.archivo}"
        )


    # ==============================
    # MOSTRAR DATOS
    # ==============================

    print(
        "\n===== DATOS EXTRAÍDOS ====="
    )

    for doc in documentos:

        print(
            f"\nArchivo: {doc.archivo}"
        )

        print(
            f"Tipo: {doc.tipo}"
        )

        print(
            doc.datos
        )


    # ==============================
    # EJECUTAR VALIDACIONES
    # ==============================

    print(
        "\n===== VALIDACIONES ====="
    )

    resultado = ejecutar_validaciones(
        documentos
    )


    for r in resultado:

        print(
            r
        )


    # ==============================
    # GUARDAR VALIDACIONES
    # ==============================

    try:

        guardar_validaciones(
            resultado
        )

        print(
            "\nValidaciones guardadas en Supabase."
        )

    except Exception as e:

        print(
            "\nError guardando validaciones:"
        )

        print(
            str(e)
        )


    print(
        "\nProceso terminado correctamente."
    )


    return documentos, resultado


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
