import os
import json
from dotenv import load_dotenv
from google import genai


# ============================================================
# CARGAR VARIABLES DE ENTORNO
# ============================================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError(
        "ERROR: No se encontró GEMINI_API_KEY. "
        "Verifica los Secrets de Streamlit."
    )


# ============================================================
# CLIENTE GEMINI
# ============================================================

client = genai.Client(
    api_key=API_KEY
)


MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.5-flash-lite"
)


# ============================================================
# PROMPTS
# IMPORTANTE:
# Las llaves JSON se escriben como {{ y }}
# porque posteriormente usamos .format(texto=texto)
# ============================================================

PROMPTS = {

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

No inventes información.

Si algún dato no aparece escribe null.

Contenido del documento:

{texto}
""",


    "DUTA": """
Eres un analista documental experto en operaciones
de Zona Franca de Colombia.

Analiza el siguiente Documento Único de Tránsito
Aduanero (DUTA).

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

- "destinatario" corresponde al consignatario
  o destinatario final de la mercancía.

- "usuario_zona_franca" corresponde al Usuario
  Industrial o Usuario de Zona Franca.

- No inventes información.

- Si un dato no existe escribe null.

Contenido del documento:

{texto}
""",


    "FACTURA COMERCIAL": """
Eres un analista documental experto en comercio exterior.

Analiza la siguiente Factura Comercial.

Extrae únicamente la información solicitada.

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

IMPORTANTE:

- "nit" corresponde al NIT del comprador,
  cuando aparezca en el documento.

- "razon_social" corresponde al nombre
  o razón social del comprador.

- "direccion" corresponde a la dirección
  del comprador.

- "valor_factura" debe corresponder al valor
  total de la factura.

- No inventes información.

- Si algún dato no existe escribe null.

Contenido del documento:

{texto}
""",


    "BL": """
Eres un analista documental experto
en transporte internacional.

Analiza el siguiente Bill of Lading (BL).

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

- "consignee" corresponde al destinatario
  o consignatario de la mercancía.

- "usuario_zona_franca" corresponde al Usuario
  Industrial de Zona Franca cuando aparezca.

- No inventes información.

- Si un dato no existe escribe null.

Contenido del documento:

{texto}
""",


    "PACKING LIST": """
Eres un analista documental experto
en comercio exterior.

Analiza el siguiente Packing List.

Responde exclusivamente un JSON válido.

{{
  "tipo_documento": "PACKING LIST",
  "numero_documento": null,
  "peso_bruto": null,
  "peso_neto": null,
  "cantidad_bultos": null
}}

No inventes información.

Si algún dato no aparece escribe null.

Contenido del documento:

{texto}
""",


    "CERTIFICADO DE FLETES": """
Eres un analista documental experto
en transporte internacional y comercio exterior.

Analiza el siguiente Certificado de Fletes
o documento de transporte.

Responde exclusivamente un JSON válido.

{{
  "tipo_documento": "CERTIFICADO DE FLETES",
  "numero_documento": null,
  "empresa_transporte": null,
  "valor_flete": null,
  "moneda": null,
  "origen": null,
  "destino": null
}}

No inventes información.

Si algún dato no aparece escribe null.

Contenido del documento:

{texto}
""",


    "DOCUMENTO DESCONOCIDO": """
Analiza el documento proporcionado.

Determina si corresponde a alguno
de los siguientes tipos:

- RUT
- DUTA
- FACTURA COMERCIAL
- BL
- PACKING LIST
- CERTIFICADO DE FLETES

Responde exclusivamente un JSON válido.

{{
  "tipo_documento": "TIPO IDENTIFICADO O DESCONOCIDO"
}}

No inventes información.

Contenido del documento:

{texto}
"""
}


# ============================================================
# LIMPIAR RESPUESTA DE GEMINI
# ============================================================

def limpiar_respuesta(respuesta):

    texto_json = respuesta.text.strip()

    # Eliminar bloques Markdown
    texto_json = texto_json.replace("```json", "")
    texto_json = texto_json.replace("```JSON", "")
    texto_json = texto_json.replace("```", "")

    texto_json = texto_json.strip()

    return json.loads(texto_json)


# ============================================================
# EXTRAER DATOS DESDE TEXTO
# ============================================================

def extraer_datos(tipo_documento, texto):

    prompt_base = PROMPTS.get(
        tipo_documento,
        PROMPTS["DOCUMENTO DESCONOCIDO"]
    )

    # Aquí solo reemplazamos {texto}
    prompt = prompt_base.format(
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
            "respuesta_original": (
                respuesta.text
                if "respuesta" in locals()
                else None
            )
        }

    except Exception as e:

        return {
            "error": f"Error extrayendo datos con Gemini: {str(e)}"
        }


# ============================================================
# ANALIZAR PDF DIRECTAMENTE CON GEMINI
# ============================================================

def analizar_pdf_con_gemini(
    ruta_pdf,
    tipo_documento="DOCUMENTO DESCONOCIDO"
):

    """
    Envía directamente un PDF a Gemini.

    Es útil para documentos escaneados donde
    PyMuPDF no puede extraer texto correctamente.
    """

    archivo_gemini = None

    try:

        print("Enviando PDF directamente a Gemini...")

        archivo_gemini = client.files.upload(
            file=ruta_pdf
        )

        prompt = PROMPTS.get(
            tipo_documento,
            PROMPTS["DOCUMENTO DESCONOCIDO"]
        )

        # Como aquí no estamos usando texto,
        # eliminamos el marcador {texto}
        prompt = prompt.replace(
            "{texto}",
            "Analiza directamente el contenido visual del PDF."
        )

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
            "error": "Gemini no devolvió un JSON válido."
        }

    except Exception as e:

        return {
            "error": f"Error analizando PDF con Gemini: {str(e)}"
        }

    finally:

        if archivo_gemini:

            try:

                client.files.delete(
                    name=archivo_gemini.name
                )

            except Exception:

                pass
