from dotenv import load_dotenv
import os
from pathlib import Path

# Cargar variables del archivo .env
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

        print("=" * 60)
        print("Procesando:", archivo.name)

        texto = leer_pdf(str(archivo))

        print("\nPrimeros 600 caracteres:")
        print(texto[:600])
        print("-" * 80)

        tipo = clasificar_documento(texto)

        print(f"Tipo detectado por texto: {tipo}")
        
        
        # Si el PDF no tiene suficiente texto o no pudo ser identificado,
        # Gemini analiza directamente el archivo PDF.
        if tipo == "DOCUMENTO DESCONOCIDO" or len(texto.strip()) < 100:
        
            print("PDF sin texto suficiente. Analizando directamente con Gemini...")
        
            resultado_gemini = analizar_pdf_con_gemini(
                str(archivo),
                "DOCUMENTO DESCONOCIDO"
            )
        
            tipo_detectado = resultado_gemini.get(
                "tipo_documento",
                "DOCUMENTO DESCONOCIDO"
            )
        
            tipo = tipo_detectado
        
            print(f"Tipo detectado por Gemini: {tipo}")
        
            # Ahora Gemini vuelve a analizar el PDF,
            # pero usando el prompt específico del documento.
            datos = analizar_pdf_con_gemini(
                str(archivo),
                tipo
            )
        
        else:
        
            datos = extraer_datos(
                tipo,
                texto
            )
        
            

        print("\nDatos extraídos por Gemini:")
        print(datos)

        datos = normalizar(datos)

        print("\nDatos normalizados:")
        print(datos)

        documento = Documento(
            tipo=tipo,
            archivo=archivo.name,
            datos=datos
        )

        documentos.append(documento)

        guardar_documento(documento)

    print("\nResumen")

    for doc in documentos:
        print(doc.tipo, "-", doc.archivo)

    print("\nVALIDACIONES")

    print("\n===== DOCUMENTOS EXTRAÍDOS =====")

    for doc in documentos:
        print(f"\nTipo: {doc.tipo}")
        print(doc.datos)
        
    resultado = ejecutar_validaciones(documentos)

    for r in resultado:
        print(r)

    guardar_validaciones(resultado)

    print("Proceso terminado correctamente.")

    return documentos, resultado


if __name__ == "__main__":

    print("Gemini API cargada:", GEMINI_API_KEY is not None)
    print("Supabase URL:", SUPABASE_URL)
    print("Supabase Key cargada:", SUPABASE_KEY is not None)

    procesar_expediente()
