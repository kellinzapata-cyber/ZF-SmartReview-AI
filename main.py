import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

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


def procesar_expediente(carpeta="documentos_prueba"):

    carpeta = Path(carpeta)

    documentos = []

    for archivo in carpeta.glob("*.pdf"):

        print("\n" + "=" * 70)
        print(f"Procesando: {archivo.name}")
        print("=" * 70)

        # -------------------------------------------------
        # 1. INTENTAR EXTRAER TEXTO DEL PDF
        # -------------------------------------------------

        texto = leer_pdf(str(archivo))

        print("\nPrimeros 600 caracteres:")

        if texto:
            print(texto[:600])
        else:
            print("[PDF SIN TEXTO EXTRAÍBLE]")

        print("-" * 70)

        # -------------------------------------------------
        # 2. CASO PDF CON TEXTO
        # -------------------------------------------------

        if texto and texto.strip():

            tipo = clasificar_documento(texto)

            print(f"\nTipo detectado por reglas: {tipo}")

            # Si las reglas no reconocen el documento,
            # Gemini intenta identificarlo directamente.
            if tipo == "DOCUMENTO DESCONOCIDO":

                print("\nDocumento no reconocido por reglas.")
                print("Solicitando identificación a Gemini...")

                identificacion = analizar_pdf_con_gemini(
                    str(archivo),
                    "DOCUMENTO DESCONOCIDO"
                )

                tipo = identificacion.get(
                    "tipo_documento",
                    "DOCUMENTO DESCONOCIDO"
                )

                print(f"Tipo identificado por Gemini: {tipo}")

            # Si finalmente conocemos el tipo,
            # extraemos los datos usando el texto.
            if tipo != "DOCUMENTO DESCONOCIDO":

                print("\nExtrayendo datos...")

                datos = extraer_datos(
                    tipo,
                    texto
                )

            else:

                datos = {
                    "tipo_documento": "DOCUMENTO DESCONOCIDO"
                }

        # -------------------------------------------------
        # 3. CASO PDF ESCANEADO O SIN TEXTO
        # -------------------------------------------------

        else:

            print("\nPDF sin texto extraíble.")
            print("Enviando PDF directamente a Gemini...")

            # Primera llamada:
            # identificar el tipo del documento
            identificacion = analizar_pdf_con_gemini(
                str(archivo),
                "DOCUMENTO DESCONOCIDO"
            )

            tipo = identificacion.get(
                "tipo_documento",
                "DOCUMENTO DESCONOCIDO"
            )

            print(f"\nTipo identificado por Gemini: {tipo}")

            # Segunda llamada:
            # extraer todos los datos del tipo identificado
            if tipo != "DOCUMENTO DESCONOCIDO":

                print("\nExtrayendo información completa del PDF...")

                datos = analizar_pdf_con_gemini(
                    str(archivo),
                    tipo
                )

            else:

                datos = identificacion

        # -------------------------------------------------
        # 4. LIMPIAR Y VALIDAR TIPO
        # -------------------------------------------------

        if not isinstance(datos, dict):

            datos = {
                "error": "La extracción no devolvió un diccionario válido."
            }

        # Forzamos el tipo correcto
        datos["tipo_documento"] = tipo

        print("\nDatos extraídos por Gemini:")
        print(datos)

        # -------------------------------------------------
        # 5. NORMALIZAR DATOS
        # -------------------------------------------------

        datos = normalizar(datos)

        print("\nDatos normalizados:")
        print(datos)

        # -------------------------------------------------
        # 6. CREAR OBJETO DOCUMENTO
        # -------------------------------------------------

        documento = Documento(
            tipo=tipo,
            archivo=archivo.name,
            datos=datos
        )

        documentos.append(documento)

        # -------------------------------------------------
        # 7. GUARDAR DOCUMENTO EN SUPABASE
        # -------------------------------------------------

        try:

            guardar_documento(documento)

            print(
                f"\nDocumento guardado correctamente: "
                f"{archivo.name}"
            )

        except Exception as e:

            print(
                f"\nAdvertencia: no fue posible guardar "
                f"{archivo.name} en Supabase."
            )

            print(str(e))

    # -------------------------------------------------
    # RESUMEN
    # -------------------------------------------------

    print("\n" + "=" * 70)
    print("RESUMEN DE DOCUMENTOS")
    print("=" * 70)

    for doc in documentos:

        print(
            f"\nArchivo: {doc.archivo}"
        )

        print(
            f"Tipo: {doc.tipo}"
        )

        print(
            f"Datos: {doc.datos}"
        )

    # -------------------------------------------------
    # VALIDACIONES
    # -------------------------------------------------

    print("\n" + "=" * 70)
    print("VALIDACIONES")
    print("=" * 70)

    resultado = ejecutar_validaciones(documentos)

    for r in resultado:

        print("\n", r)

    # -------------------------------------------------
    # GUARDAR VALIDACIONES
    # -------------------------------------------------

    try:

        guardar_validaciones(resultado)

        print(
            "\nValidaciones guardadas correctamente."
        )

    except Exception as e:

        print(
            "\nAdvertencia: no fue posible guardar "
            "las validaciones en Supabase."
        )

        print(str(e))

    print("\nProceso terminado correctamente.")

    return documentos, resultado


if __name__ == "__main__":

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
