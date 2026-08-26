import os
import json
from dotenv import load_dotenv
from google import genai


# ==================================================
# CONFIGURACIÓN
# ==================================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError(
        "ERROR: No se encontró GEMINI_API_KEY. "
        "Verifica los Secrets de Streamlit."
    )


client = genai.Client(
    api_key=API_KEY
)


MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.5-flash-lite"
)


# ==================================================
# PROMPTS PARA CADA TIPO DE DOCUMENTO
# ==================================================

PROMPTS = {

    # --------------------------------------------------
    # RUT
    # --------------------------------------------------

    "RUT": """
Eres un analista documental experto de la DIAN.

Analiza el siguiente Registro Único Tributario (RUT).

Extrae únicamente la siguiente información.

Responde exclusivamente un JSON válido.

{{
    "tipo_documento": "RUT",
    "nit": null,
    "razon_social": null,
    "direccion": null,
    "municipio": null,
    "departamento": null,
    "estado": null,
    "responsabilidades": null
}}

Instrucciones:

- No inventes información.
- Si algún dato no aparece escribe null.

Contenido del documento:

{texto}
""",


    # --------------------------------------------------
    # DUTA
    # --------------------------------------------------

    "DUTA": """
Eres un analista documental experto en operaciones de
Zona Franca de Colombia.

Analiza el siguiente Documento Único de Tránsito Aduanero
(DUTA).

Extrae únicamente la siguiente información.

Responde exclusivamente un JSON válido.

{{
    "tipo_documento": "DUTA",
    "numero_documento": null,
    "destinatario": null,
    "usuario_zona_franca": null,
    "incoterm": null,
    "moneda": null,
    "valor_factura": null,
    "peso_bruto": null,
    "peso_neto": null
}}

Instrucciones:

- "destinatario" corresponde al consignatario o
  destinatario final de la mercancía.

- "usuario_zona_franca" corresponde al Usuario Industrial
  o Usuario de Zona Franca.

- No inventes información.

- Si un dato no existe escribe null.

Contenido del documento:

{texto}
""",


    # --------------------------------------------------
    # FACTURA COMERCIAL
    # --------------------------------------------------

    "FACTURA COMERCIAL": """
Eres un analista documental experto en comercio exterior.

Analiza la siguiente factura comercial.

Extrae únicamente la siguiente información.

Responde exclusivamente un JSON válido.

{{
    "tipo_documento": "FACTURA COMERCIAL",
    "numero_factura": null,
    "vendedor": null,
    "comprador": null,
    "nit": null,
    "razon_social": null,
    "direccion": null,
    "incoterm": null,
    "moneda": null,
    "valor_factura": null,
    "descripcion_mercancia": null
}}

Instrucciones:

- "nit" corresponde al NIT del comprador cuando aparezca.

- "razon_social" corresponde al nombre o razón social
  del comprador.

- "direccion" corresponde a la dirección del comprador.

- No inventes información.

- Si algún dato no existe escribe null.

Contenido del documento:

{texto}
""",


    # --------------------------------------------------
    # BILL OF LADING
    # --------------------------------------------------

    "BL": """
Eres un analista documental experto en transporte
internacional.

Analiza el siguiente Bill of Lading (BL).

Extrae únicamente la siguiente información.

Responde exclusivamente un JSON válido.

{{
    "tipo_documento": "BL",
    "numero_bl": null,
    "shipper": null,
    "consignee": null,
    "notify_party": null,
    "usuario_zona_franca": null,
    "puerto_origen": null,
    "puerto_destino": null,
    "peso_bruto": null,
    "peso_neto": null
}}

Instrucciones:

- "consignee" es el destinatario de la mercancía.

- "usuario_zona_franca" corresponde al Usuario Industrial
  cuando aparezca.

- No inventes información.

- Si un dato no existe escribe null.

Contenido del documento:

{texto}
""",


    # --------------------------------------------------
    # PACKING LIST
    # --------------------------------------------------

    "PACKING LIST": """
Eres un analista documental experto en comercio exterior.

Analiza el siguiente Packing List.

Extrae únicamente la siguiente información.

Responde exclusivamente un JSON válido.

{{
    "tipo_documento": "PACKING LIST",
    "numero_documento": null,
    "peso_bruto": null,
    "peso_neto": null,
    "cantidad_bultos": null
}}

Instrucciones:

- No inventes información.

- Si un dato no existe escribe null.

Contenido del documento:

{texto}
""",


    # --------------------------------------------------
    # CERTIFICADO DE FLETES
    # --------------------------------------------------

    "CERTIFICADO DE FLETES": """
Eres un analista documental experto en transporte y
comercio exterior.

Analiza el siguiente Certificado o Documento de Fletes.

Extrae la información relevante del documento.

Responde exclusivamente un JSON válido.

{{
    "tipo_documento": "CERTIFICADO DE FLETES",
    "numero_documento": null,
    "transportador": null,
    "valor_flete": null,
    "moneda": null
}}

No inventes información.

Si algún dato no aparece escribe null.

Contenido del documento:

{texto}
""",


    # --------------------------------------------------
    # DOCUMENTO DESCONOCIDO
    # --------------------------------------------------

    "DOCUMENTO DESCONOCIDO": """
Analiza cuidadosamente el documento proporcionado.

Determina a cuál de las siguientes categorías pertenece:

- RUT
- DUTA
- FACTURA COMERCIAL
- BL
- PACKING LIST
- CERTIFICADO DE FLETES

Responde exclusivamente un JSON válido.

El resultado debe tener exactamente esta estructura:

{{
    "tipo_documento": "RUT | DUTA | FACTURA COMERCIAL | BL | PACKING LIST | CERTIFICADO DE FLETES | DOCUMENTO DESCONOCIDO"
}}

No agregues explicaciones.
No inventes información.
"""
}


# ==================================================
# LIMPIAR RESPUESTA DE GEMINI
# ==================================================

def limpiar_respuesta(respuesta):

    texto_respuesta = respuesta.text.strip()

    texto_respuesta = texto_respuesta.replace(
        "```json",
        ""
    )

    texto_respuesta = texto_respuesta.replace(
        "```",
        ""
    )

    texto_respuesta = texto_respuesta.strip()

    return json.loads(texto_respuesta)


# ==================================================
# EXTRAER DATOS DESDE TEXTO
# ==================================================

def extraer_datos(tipo_documento, texto):

    prompt = PROMPTS.get(
        tipo_documento,
        PROMPTS["DOCUMENTO DESCONOCIDO"]
    )

    prompt = prompt.format(
        texto=texto
    )

    try:

        respuesta = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )

        return limpiar_respuesta(respuesta)

    except json.JSONDecodeError:

        return {
            "error": "Gemini no devolvió un JSON válido.",
            "respuesta_original": respuesta.text
        }

    except Exception as e:

        return {
            "error": f"Error al extraer datos con Gemini: {str(e)}"
        }


# ==================================================
# ANALIZAR PDF DIRECTAMENTE CON GEMINI
# ==================================================

def analizar_pdf_con_gemini(
    ruta_pdf,
    tipo_documento="DOCUMENTO DESCONOCIDO"
):

    """
    Envía directamente el PDF a Gemini.

    Se utiliza principalmente cuando el PDF es una imagen
    escaneada y PyMuPDF no logra extraer texto.
    """

    archivo_gemini = None

    try:

        print(
            "Enviando PDF directamente a Gemini..."
        )

        # Subir el archivo PDF
        archivo_gemini = client.files.upload(
            file=ruta_pdf
        )

        # Obtener el prompt correspondiente
        prompt = PROMPTS.get(
            tipo_documento,
            PROMPTS["DOCUMENTO DESCONOCIDO"]
        )

        # Analizar el PDF con Gemini
        respuesta = client.models.generate_content(
            model=MODEL,
            contents=[
                prompt,
                archivo_gemini
            ]
        )

        return limpiar_respuesta(respuesta)

    except json.JSONDecodeError:

        return {
            "error": "Gemini no devolvió un JSON válido.",
            "respuesta_original": (
                respuesta.text
                if "respuesta" in locals()
                else None
            )
        }

    except Exception as e:

        return {
            "error": (
                "Error analizando PDF con Gemini: "
                f"{str(e)}"
            )
        }

    finally:

        # Eliminar archivo temporal de Gemini
        if archivo_gemini:

            try:

                client.files.delete(
                    name=archivo_gemini.name
                )

            except Exception:

                pass
