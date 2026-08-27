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
Eres un analista documental experto de la DIAN de Colombia.

Analiza cuidadosamente el Registro Único Tributario (RUT).

Extrae exclusivamente la información solicitada.

IMPORTANTE:

- El NIT debe corresponder al número de identificación de la persona jurídica.
- Si el documento muestra un dígito de verificación, inclúyelo separado por guion.
- La razón social debe copiarse tal como aparece en el RUT.
- La dirección debe corresponder a la dirección principal registrada.
- No confundas números de formularios con el NIT.
- No inventes información.

Responde exclusivamente un JSON válido.

{
  "tipo_documento": "RUT",
  "nit": null,
  "razon_social": null,
  "direccion": null,
  "municipio": null,
  "departamento": null,
  "estado": null,
  "responsabilidades": null
}

Contenido del documento:

{texto}
""",


    "DUTA": """
Eres un analista documental experto en operaciones aduaneras y Zona Franca de Colombia.

Analiza cuidadosamente el Documento Único de Tránsito Aduanero.

Extrae exclusivamente los siguientes datos.

IMPORTANTE PARA EL VALOR DE LA FACTURA:

- "valor_factura" debe ser el valor TOTAL de la factura comercial asociado a la operación.
- No extraigas valores unitarios.
- No extraigas cantidades de mercancía.
- No extraigas valores de fletes, seguros o tributos.
- Busca expresamente el valor total declarado de la factura comercial.
- Conserva el número completo con sus decimales.

IMPORTANTE:

- "destinatario" corresponde al consignatario o destinatario final.
- "usuario_zona_franca" corresponde al Usuario Industrial o Usuario de Zona Franca.
- No inventes información.

Responde exclusivamente un JSON válido.

{
  "tipo_documento": "DUTA",
  "numero_documento": null,
  "destinatario": null,
  "usuario_zona_franca": null,
  "incoterm": null,
  "moneda": null,
  "valor_factura": null,
  "peso_bruto": null,
  "peso_neto": null
}

Contenido del documento:

{texto}
""",


    "FACTURA COMERCIAL": """
Eres un analista documental experto en comercio exterior.

Analiza cuidadosamente la Factura Comercial.

Extrae exclusivamente la información solicitada.

IMPORTANTE PARA "valor_factura":

- Debe ser el valor TOTAL de la factura.
- Busca campos como:
  TOTAL INVOICE VALUE
  TOTAL
  GRAND TOTAL
  TOTAL AMOUNT
  INVOICE TOTAL
  TOTAL VALUE
- NO extraigas el valor unitario de los productos.
- NO extraigas el precio por unidad.
- NO extraigas cantidades.
- NO extraigas subtotales si existe un total final.
- Conserva el valor completo con sus decimales.

IMPORTANTE PARA EL COMPRADOR:

- "nit" corresponde al NIT del comprador o destinatario colombiano.
- "razon_social" corresponde a la razón social del comprador.
- "direccion" corresponde a la dirección del comprador.
- No confundas vendedor con comprador.

No inventes información.

Responde exclusivamente un JSON válido.

{
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
}

Contenido del documento:

{texto}
""",


    "BL": """
Eres un analista documental experto en transporte internacional.

Analiza cuidadosamente el Bill of Lading.

Extrae exclusivamente los datos solicitados.

IMPORTANTE:

- "consignee" corresponde al destinatario de la mercancía.
- "usuario_zona_franca" corresponde al Usuario Industrial cuando aparezca.
- No inventes información.

Responde exclusivamente un JSON válido.

{
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
}

Contenido del documento:

{texto}
""",


    "PACKING LIST": """
Eres un analista documental experto en comercio exterior.

Analiza cuidadosamente el Packing List.

Extrae exclusivamente la información solicitada.

IMPORTANTE:

- "peso_bruto" corresponde al peso bruto total.
- "peso_neto" corresponde al peso neto total.
- "cantidad_bultos" corresponde al número total de bultos.
- No confundas cantidades de productos con cantidad de bultos.

No inventes información.

Responde exclusivamente un JSON válido.

{
  "tipo_documento": "PACKING LIST",
  "numero_documento": null,
  "peso_bruto": null,
  "peso_neto": null,
  "cantidad_bultos": null
}

Contenido del documento:

{texto}
""",


    "DOCUMENTO DESCONOCIDO": """
Analiza cuidadosamente el documento.

Determina si corresponde a alguno de los siguientes tipos:

- RUT
- DUTA
- FACTURA COMERCIAL
- BL
- PACKING LIST
- CERTIFICADO DE FLETES

Responde exclusivamente un JSON válido:

{
  "tipo_documento": "TIPO IDENTIFICADO O DESCONOCIDO"
}

No inventes información.
"""
}


def limpiar_respuesta(respuesta):

    texto_json = respuesta.text.strip()

    texto_json = texto_json.replace("```json", "")
    texto_json = texto_json.replace("```", "")
    texto_json = texto_json.strip()

    return json.loads(texto_json)


def extraer_datos(tipo_documento, texto):

    prompt = PROMPTS.get(
        tipo_documento,
        PROMPTS["DOCUMENTO DESCONOCIDO"]
    ).format(texto=texto)

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
            "error": f"Error extrayendo datos: {str(e)}"
        }


def analizar_pdf_con_gemini(ruta_pdf, tipo_documento):

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
