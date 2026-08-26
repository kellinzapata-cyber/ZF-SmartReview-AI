import os
import json
from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
print("GEMINI_API_KEY encontrada:", bool(API_KEY))
print("Longitud de la clave:", len(API_KEY) if API_KEY else 0)
print("Modelo configurado:", os.getenv("GEMINI_MODEL"))

if not API_KEY:
    raise ValueError(
        "ERROR: No se encontró GEMINI_API_KEY. "
        "Verifica los Secrets de Streamlit."
    )

client = genai.Client(
    api_key=API_KEY
)

PROMPTS = {

    "RUT": """
Eres un analista documental experto de la DIAN.

Analiza el siguiente Registro Único Tributario (RUT) y extrae únicamente la siguiente información.

Responde exclusivamente un JSON válido.

{{
  "tipo_documento": "RUT",
  "nit": "",
  "razon_social": "",
  "direccion": "",
  "municipio": "",
  "departamento": "",
  "estado": "",
  "responsabilidades": ""
}}

Si algún dato no aparece escribe null.

Texto:

{texto}
""",

 "DUTA": """
Eres un analista documental experto en operaciones de Zona Franca de Colombia.

Analiza el siguiente Documento Único de Tránsito Aduanero (DUTA).

Extrae únicamente la siguiente información.

Responde EXCLUSIVAMENTE un JSON válido.

{{
  "tipo_documento":"DUTA",
  "numero_documento":"",
  "destinatario":"",
  "usuario_zona_franca":"",
  "incoterm":"",
  "moneda":"",
  "valor_factura":"",
  "peso_bruto":"",
  "peso_neto":""
}}

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
