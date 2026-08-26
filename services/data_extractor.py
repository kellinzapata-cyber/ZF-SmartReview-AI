import os
import json
from dotenv import load_dotenv
from google import genai

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


PROMPTS = {

    "RUT": """
Eres un analista documental experto de la DIAN.

Analiza el siguiente Registro Único Tributario (RUT) y extrae únicamente la siguiente información.

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
Eres un analista documental experto en operaciones de Zona Franca de Colombia.

Analiza el siguiente Documento Único de Tránsito Aduanero (DUTA).

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

- "destinatario" corresponde al consignatario o destinatario final.
- "usuario_zona_franca" corresponde al Usuario Industrial o Usuario de Zona Franca.
- No inventes información.
- Si un dato no existe escribe null.

Contenido del documento:

{texto}
""",

    "FACTURA COMERCIAL": """
Eres un analista documental experto en comercio exterior.

Analiza la siguiente factura comercial.

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

- "nit" corresponde al NIT del comprador cuando aparezca.
- "razon_social" corresponde al nombre o razón social del comprador.
- "direccion" corresponde a la dirección del comprador.
- No inventes información.
- Si algún dato no existe escribe null.

Contenido del documento:

{texto}
""",

    "BL": """
Eres un analista documental experto en transporte internacional.

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

- "consignee" es el destinatario de la mercancía.
- "usuario_zona_franca" corresponde al Usuario Industrial cuando aparezca.
- No inventes información.
- Si un dato no existe escribe null.

Contenido del documento:

{texto}
""",

    "PACKING LIST": """
Eres un analista documental.

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
Si un dato no existe escribe null.

Contenido del documento:

{texto}
""",

    "DOCUMENTO DESCONOCIDO": """
Analiza el documento proporcionado.

Determina si corresponde a alguno de los siguientes tipos:

- RUT
- DUTA
- FACTURA COMERCIAL
- BL
- PACKING LIST
- CERTIFICADO DE FLETES

Responde exclusivamente un JSON válido:

{{
  "tipo_documento": "TIPO IDENTIFICADO O DESCONOCIDO"
}}

No inventes información.
"""
}


def limpiar_respuesta(respuesta):

    texto_json = (
        respuesta.text
        .replace("```json", "")
        .replace("```", "")
        .strip()
    )

    return json.loads(texto_json)


def extraer_datos(tipo_documento, texto):

    prompt = PROMPTS.get(
        tipo_documento,
        PROMPTS["DOCUMENTO DESCONOCIDO"]
    ).format(texto=texto)

    respuesta = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    try:
        return limpiar_respuesta(respuesta)

    except json.JSONDecodeError:

        return {
            "error": "Gemini no devolvió un JSON válido.",
            "respuesta_original": respuesta.text
        }


def analizar_pdf_con_gemini(ruta_pdf, tipo_documento="DOCUMENTO DESCONOCIDO"):

    """
    Envía directamente un PDF a Gemini.
    Es especialmente útil cuando el PDF es escaneado
    y PyMuPDF no puede extraer texto.
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

        respuesta = client.models.generate_content(
            model=MODEL,
            contents=[
                prompt,
                archivo_gemini
            ]
        )

        return limpiar_respuesta(respuesta)

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
Instrucciones:

- "destinatario" corresponde al consignatario o destinatario final de la mercancía.
- "usuario_zona_franca" corresponde al Usuario Industrial o Usuario de Zona Franca.
- No inventes información.
- Si un dato no existe escribe null.

Texto:

{texto}
""",

    "FACTURA COMERCIAL": """
Eres un analista documental experto en comercio exterior.

Analiza la siguiente factura comercial.

Responde únicamente un JSON válido.

{{

  "tipo_documento":"FACTURA COMERCIAL",
  "numero_factura":"",
  "vendedor":"",
  "comprador":"",
  "nit":"",
  "razon_social":"",
  "direccion":"",
  "incoterm":"",
  "moneda":"",
  "valor_factura":"",
  "descripcion_mercancia":""

}}

- "nit" corresponde al NIT del comprador cuando aparezca.
- "razon_social" corresponde al nombre o razón social del comprador.
- "direccion" corresponde a la dirección del comprador.
- Si algún dato no existe, escribe null.

Texto:

{texto}
""",

    "BL": """
Eres un analista documental experto en transporte internacional.

Analiza el siguiente Bill of Lading (BL).

Responde únicamente un JSON válido.

{{
  "tipo_documento":"BL",
  "numero_bl":"",
  "shipper":"",
  "consignee":"",
  "notify_party":"",
  "usuario_zona_franca":"",
  "puerto_origen":"",
  "puerto_destino":"",
  "peso_bruto":"",
  "peso_neto":""
}}

Instrucciones:

- "consignee" es el destinatario de la mercancía.
- "usuario_zona_franca" corresponde al Usuario Industrial cuando aparezca.
- No inventes información.
- Si un dato no existe escribe null.

Texto:

{texto}
""",

    "PACKING LIST": """
Eres un analista documental.

Analiza el siguiente Packing List.

Responde únicamente un JSON válido.

{{
  "tipo_documento":"PACKING LIST",
  "numero_documento":"",
  "peso_bruto":"",
  "peso_neto":"",
  "cantidad_bultos":""
}}

Si un dato no existe escribe null.

Texto:

{texto}
""",

    "DOCUMENTO DESCONOCIDO": """
Analiza el siguiente documento y responde únicamente un JSON.

{{
  "tipo_documento":"DESCONOCIDO"
}}

Texto:

{texto}
"""
}


def extraer_datos(tipo_documento, texto):

    prompt = PROMPTS.get(
        tipo_documento,
        PROMPTS["DOCUMENTO DESCONOCIDO"]
    ).format(texto=texto)

    MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

    respuesta = client.models.generate_content(
    model=MODEL,
    contents=prompt
    )

    texto_json = (
        respuesta.text
        .replace("```json", "")
        .replace("```", "")
        .strip()
    )

    try:
        return json.loads(texto_json)

    except json.JSONDecodeError:
        return {
            "error": "Gemini no devolvió un JSON válido.",
            "respuesta_original": texto_json
        }
