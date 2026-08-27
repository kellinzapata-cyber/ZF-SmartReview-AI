import os
from pathlib import Path
from dotenv import load_dotenv


# ==========================================================
# CARGAR VARIABLES DE ENTORNO
# ==========================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


# ==========================================================
# IMPORTAR SERVICIOS
# ==========================================================

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


# ==========================================================
# FUNCIÓN PARA MOSTRAR INFORMACIÓN DEL DOCUMENTO
# ==========================================================

def mostrar_resumen_documento(documento):

    print("\n" + "=" * 60)

    print("DOCUMENTO PROCESADO")

    print("=" * 60)

    print(f"Archivo: {documento.archivo}")

    print(f"Tipo: {documento.tipo}")

    print("\nDatos extraídos:")

    for clave, valor in documento.datos.items():

        print(
            f"{clave}: {valor}"
        )

    print("=" * 60)


# ==========================================================
# PROCESAR UN DOCUMENTO
# ==========================================================

def procesar_documento(archivo):

    print("\n" + "=" * 80)

    print(f"Procesando: {archivo.name}")

    print("=" * 80)


    # ------------------------------------------------------
    # 1. LEER PDF
    # ------------------------------------------------------

    try:

        texto = leer_pdf(
            str(archivo)
        )

    except Exception as e:

        print(
            f"Error leyendo el PDF {archivo.name}: {e}"
        )

        texto = ""


    # ------------------------------------------------------
    # 2. MOSTRAR TEXTO EXTRAÍDO
    # ------------------------------------------------------

    print("\nPrimeros 600 caracteres:")

    print("-" * 80)

    print(
        texto[:600]
        if texto
        else "[No se pudo extraer texto del PDF]"
    )

    print("-" * 80)


    # ------------------------------------------------------
    # 3. CLASIFICAR DOCUMENTO
    # ------------------------------------------------------

    tipo = "DOCUMENTO DESCONOCIDO"


    # Solo intentar clasificación por texto
    # si realmente se extrajo texto.

    if texto and len(texto.strip()) > 20:

        tipo = clasificar_documento(
            texto
        )


    print(
        f"\nTipo detectado inicialmente: {tipo}"
    )


    # ------------------------------------------------------
    # 4. DOCUMENTO ESCANEADO O SIN TEXTO
    # ------------------------------------------------------

    if not texto or len(texto.strip()) < 20:

        print(
            "\nPDF con poco o ningún texto."
        )

        print(
            "Analizando PDF directamente con Gemini..."
        )

        datos = analizar_pdf_con_gemini(
            str(archivo),
            "DOCUMENTO DESCONOCIDO"
        )


        # --------------------------------------------------
        # OBTENER TIPO IDENTIFICADO POR GEMINI
        # --------------------------------------------------

        tipo_gemini = datos.get(
            "tipo_documento"
        )

        if (
            tipo_gemini
            and tipo_gemini != "DESCONOCIDO"
            and tipo_gemini != "DOCUMENTO DESCONOCIDO"
        ):

            tipo = tipo_gemini.upper()

            print(
                f"Tipo identificado por Gemini: {tipo}"
            )


        # Si Gemini identificó un tipo válido,
        # analizamos nuevamente usando el prompt específico.

        if tipo != "DOCUMENTO DESCONOCIDO":

            print(
                "\nReanalizando con el prompt específico..."
            )

            datos = analizar_pdf_con_gemini(
                str(archivo),
                tipo
            )


    # ------------------------------------------------------
    # 5. DOCUMENTO CON TEXTO
    # ------------------------------------------------------

    else:

        # --------------------------------------------------
        # DOCUMENTO DESCONOCIDO
        # --------------------------------------------------

        if tipo == "DOCUMENTO DESCONOCIDO":

            print(
                "\nLa clasificación por reglas no identificó el documento."
            )

            print(
                "Solicitando clasificación a Gemini..."
            )

            clasificacion_gemini = extraer_datos(
                "DOCUMENTO DESCONOCIDO",
                texto
            )


            tipo_gemini = clasificacion_gemini.get(
                "tipo_documento"
            )


            if (
                tipo_gemini
                and tipo_gemini.upper()
                not in [
                    "DESCONOCIDO",
                    "DOCUMENTO DESCONOCIDO"
                ]
            ):

                tipo = tipo_gemini.upper()

                print(
                    f"Tipo identificado por Gemini: {tipo}"
                )

                print(
                    "\nExtrayendo datos con el prompt específico..."
                )

                datos = extraer_datos(
                    tipo,
                    texto
                )

            else:

                print(
                    "Gemini tampoco pudo identificar el documento."
                )

                datos = clasificacion_gemini


        # --------------------------------------------------
        # DOCUMENTO IDENTIFICADO
        # --------------------------------------------------

        else:

            print(
                "\nAnalizando texto con Gemini..."
            )

            datos = extraer_datos(
                tipo,
                texto
            )


    # ------------------------------------------------------
    # 6. VERIFICAR ERRORES DE GEMINI
    # ------------------------------------------------------

    if not isinstance(datos, dict):

        print(
            "\nADVERTENCIA: Gemini no devolvió un diccionario válido."
        )

        datos = {
            "tipo_documento": tipo,
            "error": "Respuesta inválida de Gemini"
        }


    # ------------------------------------------------------
    # 7. FORZAR TIPO DOCUMENTO CORRECTO
    # ------------------------------------------------------

    datos["tipo_documento"] = tipo


    # ------------------------------------------------------
    # 8. MOSTRAR DATOS ORIGINALES
    # ------------------------------------------------------

    print(
        "\nDatos extraídos por Gemini:"
    )

    print(datos)


    # ------------------------------------------------------
    # 9. NORMALIZAR DATOS
    # ------------------------------------------------------

    datos_normalizados = normalizar(
        datos
    )


    # Garantizar que el tipo se conserve.

    datos_normalizados[
        "tipo_documento"
    ] = tipo


    print(
        "\nDatos normalizados:"
    )

    print(
        datos_normalizados
    )


    # ------------------------------------------------------
    # 10. CREAR OBJETO DOCUMENTO
    # ------------------------------------------------------

    documento = Documento(

        tipo=tipo,

        archivo=archivo.name,

        datos=datos_normalizados

    )


    return documento


# ==========================================================
# FUNCIÓN PRINCIPAL
# ==========================================================

def procesar_expediente(
    carpeta="documentos_prueba"
):

    carpeta = Path(
        carpeta
    )


    # ------------------------------------------------------
    # VERIFICAR CARPETA
    # ------------------------------------------------------

    if not carpeta.exists():

        raise FileNotFoundError(

            f"No existe la carpeta: {carpeta}"

        )


    # ------------------------------------------------------
    # BUSCAR PDF
    # ------------------------------------------------------

    archivos = list(

        carpeta.glob(
            "*.pdf"
        )

    )


    if not archivos:

        print(
            "No se encontraron archivos PDF."
        )

        return [], []


    print(
        "\n" + "=" * 80
    )

    print(
        "INICIANDO PROCESAMIENTO DEL EXPEDIENTE"
    )

    print(
        "=" * 80
    )

    print(
        f"\nCantidad de PDFs encontrados: {len(archivos)}"
    )


    documentos = []


    # ======================================================
    # PROCESAR TODOS LOS DOCUMENTOS
    # ======================================================

    for archivo in archivos:

        try:

            documento = procesar_documento(
                archivo
            )


            documentos.append(
                documento
            )


            # --------------------------------------------------
            # GUARDAR EN SUPABASE
            # --------------------------------------------------

            try:

                guardar_documento(
                    documento
                )

                print(
                    "\nDocumento guardado en Supabase."
                )


            except Exception as e:

                print(
                    "\nADVERTENCIA:"
                )

                print(
                    f"No fue posible guardar "
                    f"{archivo.name} en Supabase."
                )

                print(
                    f"Detalle: {e}"
                )


        except Exception as e:

            print(
                "\nERROR PROCESANDO DOCUMENTO:"
            )

            print(
                archivo.name
            )

            print(
                f"Detalle: {e}"
            )


    # ======================================================
    # RESUMEN DE DOCUMENTOS
    # ======================================================

    print(
        "\n" + "=" * 80
    )

    print(
        "RESUMEN DE DOCUMENTOS"
    )

    print(
        "=" * 80
    )


    for documento in documentos:

        print(

            f"{documento.tipo} "
            f"- "
            f"{documento.archivo}"

        )


    # ======================================================
    # MOSTRAR TODOS LOS DATOS EXTRAÍDOS
    # ======================================================

    print(
        "\n" + "=" * 80
    )

    print(
        "DOCUMENTOS EXTRAÍDOS Y NORMALIZADOS"
    )

    print(
        "=" * 80
    )


    for documento in documentos:

        print(
            f"\nTIPO: {documento.tipo}"
        )

        print(
            f"ARCHIVO: {documento.archivo}"
        )

        print(
            "DATOS:"
        )

        for clave, valor in documento.datos.items():

            print(
                f"  {clave}: {valor}"
            )


    # ======================================================
    # EJECUTAR VALIDACIONES
    # ======================================================

    print(
        "\n" + "=" * 80
    )

    print(
        "EJECUTANDO VALIDACIONES"
    )

    print(
        "=" * 80
    )


    try:

        resultado = ejecutar_validaciones(
            documentos
        )


    except Exception as e:

        print(
            "\nERROR EJECUTANDO VALIDACIONES:"
        )

        print(
            e
        )

        resultado = []


    # ======================================================
    # MOSTRAR VALIDACIONES
    # ======================================================

    print(
        "\nRESULTADO DE VALIDACIONES"
    )


    for validacion in resultado:

        print(
            "\n----------------------------------------"
        )

        print(
            f"Validación: "
            f"{validacion.get('validacion')}"
        )

        print(
            f"Estado: "
            f"{validacion.get('estado')}"
        )

        print(
            f"Documento 1: "
            f"{validacion.get('valor_1')}"
        )

        print(
            f"Documento 2: "
            f"{validacion.get('valor_2')}"
        )


    # ======================================================
    # GUARDAR VALIDACIONES EN SUPABASE
    # ======================================================

    if resultado:

        try:

            guardar_validaciones(
                resultado
            )

            print(
                "\nValidaciones guardadas en Supabase."
            )


        except Exception as e:

            print(
                "\nADVERTENCIA:"
            )

            print(
                "No fue posible guardar "
                "las validaciones en Supabase."
            )

            print(
                f"Detalle: {e}"
            )


    # ======================================================
    # FINALIZAR
    # ======================================================

    print(
        "\n" + "=" * 80
    )

    print(
        "PROCESO TERMINADO CORRECTAMENTE"
    )

    print(
        "=" * 80
    )


    return documentos, resultado


# ==========================================================
# EJECUCIÓN DIRECTA
# ==========================================================

if __name__ == "__main__":

    print(
        "\nCONFIGURACIÓN DEL PROYECTO"
    )

    print(
        "Gemini API cargada:",
        GEMINI_API_KEY is not None
    )

    print(
        "Supabase URL configurada:",
        SUPABASE_URL is not None
    )

    print(
        "Supabase Key cargada:",
        SUPABASE_KEY is not None
    )


    procesar_expediente()
