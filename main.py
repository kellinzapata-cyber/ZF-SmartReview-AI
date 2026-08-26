from dotenv import load_dotenv
import os
from pathlib import Path

# Cargar variables de entorno
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Importar servicios
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

    # Recorrer todos los PDF de la carpeta
    for archivo in carpeta.glob("*.pdf"):

        print("=" * 60)
        print("Procesando:", archivo.name)

        # Leer el texto del PDF
        texto = leer_pdf(str(archivo))

        print("\nPrimeros 600 caracteres:")
        print(texto[:600])
        print("-" * 80)

        # Clasificar inicialmente usando el texto extraído
        tipo = clasificar_documento(texto)

        print(f"Tipo detectado por texto: {tipo}")

        # ==================================================
        # CASO 1:
        # El PDF tiene poco texto o no pudo ser identificado.
        # Se envía directamente el PDF a Gemini.
        # ==================================================

        if tipo == "DOCUMENTO DESCONOCIDO" or len(texto.strip()) < 100:

            print(
                "\nPDF sin texto suficiente o no identificado."
            )

            print(
                "Analizando directamente el PDF con Gemini..."
            )

            # Primero Gemini intenta identificar el documento
            resultado_identificacion = analizar_pdf_con_gemini(
                str(archivo),
                "DOCUMENTO DESCONOCIDO"
            )

            print("\nResultado de identificación:")
            print(resultado_identificacion)

            # Obtener el tipo identificado
            tipo = resultado_identificacion.get(
                "tipo_documento",
                "DOCUMENTO DESCONOCIDO"
            )

            print(
                f"\nTipo detectado por Gemini: {tipo}"
            )

            # Ahora Gemini analiza nuevamente el PDF
            # usando el prompt específico del tipo identificado
            datos = analizar_pdf_con_gemini(
                str(archivo),
                tipo
            )

        # ==================================================
        # CASO 2:
        # El PDF tiene texto y fue identificado por las reglas.
        # ==================================================

        else:

            print(
                "\nExtrayendo datos a partir del texto con Gemini..."
            )

            datos = extraer_datos(
                tipo,
                texto
            )

        # Mostrar datos extraídos
        print("\nDatos extraídos por Gemini:")
        print(datos)

        # Normalizar los datos
        datos = normalizar(datos)

        print("\nDatos normalizados:")
        print(datos)

        # Crear objeto Documento
        documento = Documento(
            tipo=tipo,
            archivo=archivo.name,
            datos=datos
        )

        # Agregar a la lista
        documentos.append(documento)

        # Guardar documento en Supabase
        guardar_documento(documento)

    # ==================================================
    # RESUMEN DE DOCUMENTOS
    # ==================================================

    print("\n" + "=" * 60)
    print("RESUMEN DE DOCUMENTOS")
    print("=" * 60)

    for doc in documentos:

        print(
            f"{doc.tipo} - {doc.archivo}"
        )

    # ==================================================
    # MOSTRAR DOCUMENTOS EXTRAÍDOS
    # ==================================================

    print("\n" + "=" * 60)
    print("DOCUMENTOS EXTRAÍDOS")
    print("=" * 60)

    for doc in documentos:

        print(f"\nArchivo: {doc.archivo}")
        print(f"Tipo: {doc.tipo}")
        print("Datos:")

        print(doc.datos)

    # ==================================================
    # EJECUTAR VALIDACIONES
    # ==================================================

    print("\n" + "=" * 60)
    print("VALIDACIONES")
    print("=" * 60)

    resultado = ejecutar_validaciones(documentos)

    for r in resultado:

        print(r)

    # Guardar validaciones en Supabase
    guardar_validaciones(resultado)

    print("\nProceso terminado correctamente.")

    # Devolver información a Streamlit
    return documentos, resultado


# ==================================================
# EJECUCIÓN DIRECTA
# ==================================================

if __name__ == "__main__":

    print(
        "Gemini API cargada:",
        GEMINI_API_KEY is not None
    )

    print(
        "Supabase URL:",
        SUPABASE_URL
    )

    print(
        "Supabase Key cargada:",
        SUPABASE_KEY is not None
    )

    procesar_expediente()
