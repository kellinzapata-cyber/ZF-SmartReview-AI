import os
import json
import re

from dotenv import load_dotenv
from google import genai


load_dotenv()


API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError(
        "ERROR: No se encontró GEMINI_API_KEY. "
        "Verifica GEMINI_API_KEY en los Secrets de Streamlit."
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
Eres un analista documental experto de la DIAN en Colombia.

Analiza exclusivamente el contenido del Registro Único Tributario proporcionado.

Extrae únicamente la información solicitada.

REGLAS IMPORTANTES:

- No inventes información.
- Copia los datos tal como aparecen en el documento.
- El NIT debe corresponder al número de identificación tributaria.
- No confundas el número del formulario con el NIT.
- No agregues información que no aparezca en el documento.
- Si un dato no aparece, responde null.

Responde exclusivamente JSON válido:

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
Eres un analista documental experto en operaciones aduaneras y Zona Franca en Colombia.

Analiza exclusivamente el Documento Único de Tránsito Aduanero proporcionado.

Extrae solamente los datos solicitados.

REGLAS IMPORTANTES:

- "numero_documento" corresponde al número del DUTA.
- "destinatario" corresponde al consignatario o destinatario final de la mercancía.
- "usuario_zona_franca" corresponde exclusivamente al Usuario Industrial, Usuario Comercial, Usuario Operador o Usuario de Zona Franca identificado en el documento.
- "incoterm" debe ser únicamente el código Incoterm, por ejemplo: FOB, CIF, EXW, DDP.
- "moneda" debe ser la moneda del valor de la factura.
- "valor_factura" debe ser exclusivamente el valor total de la factura comercial asociada a la mercancía.
- NO confundas valor factura con fletes, seguros, tributos, valor FOB u otros valores.
- "peso_bruto" debe corresponder únicamente al peso bruto total.
- "peso_neto" debe corresponder únicamente al peso neto total.
- No inventes información.
- Si un dato no aparece claramente, responde null.

Responde exclusivamente JSON válido:

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

Analiza exclusivamente la factura comercial proporcionada.

Extrae únicamente los datos solicitados.

REGLAS IMPORTANTES:

- "numero_factura" corresponde al número de la Commercial Invoice.
- "vendedor" corresponde al Seller, Exporter o proveedor.
- "comprador" corresponde al Buyer, Importer o cliente.
- "nit" corresponde únicamente al NIT o identificación tributaria del comprador cuando aparezca.
- "razon_social" corresponde al nombre o razón social del comprador.
- "direccion" corresponde a la dirección del comprador.
- "incoterm" debe ser únicamente el código del Incoterm.
- "moneda" debe corresponder a la moneda de la factura.
- "valor_factura" debe ser exclusivamente el TOTAL FINAL DE LA FACTURA.
- Para "valor_factura", busca expresiones como:
  TOTAL INVOICE VALUE,
  INVOICE TOTAL,
  TOTAL AMOUNT,
  GRAND TOTAL,
  TOTAL.
- NO uses como valor_factura:
  precio unitario,
  subtotal de una línea,
  precio de un producto,
  valor de flete,
  valor de seguro,
  impuestos,
  descuentos.
- "descripcion_mercancia" debe ser una descripción general de la mercancía.
- No inventes información.
- Si un dato no aparece claramente, responde null.

Responde exclusivamente JSON válido:

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

Analiza exclusivamente el Bill of Lading proporcionado.

Extrae solamente los datos solicitados.

REGLAS IMPORTANTES:

- "numero_bl" corresponde al número del Bill of Lading.
- "shipper" corresponde al remitente.
- "consignee" corresponde al destinatario.
- "notify_party" corresponde al Notify Party.
- "usuario_zona_franca" debe extraerse únicamente si aparece claramente identificado.
- "peso_bruto" corresponde al peso bruto total de la mercancía.
- "peso_neto" corresponde al peso neto total solamente si aparece claramente.
- No confundas pesos por bulto con el peso total.
- No inventes información.
- Si no aparece claramente, responde null.

Responde exclusivamente JSON válido:

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

Analiza exclusivamente el Packing List proporcionado.

REGLAS IMPORTANTES:

- "numero_documento" corresponde al número del Packing List.
- "peso_bruto" corresponde al peso bruto TOTAL.
- "peso_neto" corresponde al peso neto TOTAL.
- "cantidad_bultos" corresponde al número total de paquetes, cajas, pallets o bultos.
- No uses valores parciales de una línea cuando exista un total.
- No inventes información.
- Si un dato no aparece claramente, responde null.

Responde exclusivamente JSON válido:

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


    "CERTIFICADO DE FLETES": """
Eres un analista documental experto en transporte y comercio exterior.

Analiza el documento proporcionado y extrae únicamente la información que aparezca claramente.

Responde exclusivamente JSON válido:

{
  "tipo_documento": "CERTIFICADO DE FLETES",
  "numero_documento": null,
  "empresa_transportadora": null,
  "valor_flete": null,
  "moneda": null
}

No inventes información.

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

Responde exclusivamente JSON válido:

{
  "tipo_documento": "TIPO IDENTIFICADO O DESCONOCIDO"
}

Contenido del documento:

{texto}
"""
}


def limpiar_respuesta(respuesta):

    texto_json = respuesta.text.strip()

    texto_json = texto_json.replace("```json", "")
    texto_json = texto_json.replace("```", "")
    texto_json = texto_json.strip()

    # Buscar el bloque JSON si Gemini agrega texto adicional
    coincidencia = re.search(
        r"\{.*\}",
        texto_json,
        re.DOTALL
    )

    if coincidencia:
        texto_json = coincidencia.group()

    return json.loads(texto_json)


def extraer_datos(tipo_documento, texto):

    plantilla = PROMPTS.get(
        tipo_documento,
        PROMPTS["DOCUMENTO DESCONOCIDO"]
    )

    # Usamos replace para evitar errores con las llaves {}
    prompt = plantilla.replace(
        "{texto}",
        texto
    )

    try:

        respuesta = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )

        datos = limpiar_respuesta(respuesta)

        return datos

    except json.JSONDecodeError:

        return {
            "error": "Gemini no devolvió un JSON válido.",
            "respuesta_original": respuesta.text
            if "respuesta" in locals()
            else None
        }

    except Exception as e:

        return {
            "error": f"Error extrayendo datos: {str(e)}"
        }


def analizar_pdf_con_gemini(
    ruta_pdf,
    tipo_documento="DOCUMENTO DESCONOCIDO"
):

    archivo_gemini = None

    try:

        print("Enviando PDF directamente a Gemini...")

        archivo_gemini = client.files.upload(
            file=ruta_pdf
        )

        plantilla = PROMPTS.get(
            tipo_documento,
            PROMPTS["DOCUMENTO DESCONOCIDO"]
        )

        # Para PDF directo eliminamos el marcador de texto
        prompt = plantilla.replace(
            "{texto}",
            "Analiza directamente el archivo PDF adjunto."
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
