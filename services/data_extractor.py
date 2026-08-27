import os
import json

from dotenv import load_dotenv
from google import genai


# -------------------------------------------------
# CONFIGURACIÓN
# -------------------------------------------------

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:

    raise ValueError(
        "ERROR: No se encontró GEMINI_API_KEY. "
        "Verifica la configuración de Streamlit Secrets."
    )


client = genai.Client(
    api_key=API_KEY
)


MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.5-flash-lite"
)


# -------------------------------------------------
# PROMPTS
# -------------------------------------------------

PROMPTS = {


    # =============================================
    # RUT
    # =============================================

    "RUT": """
Eres un analista documental experto en documentos de la DIAN de Colombia.

Analiza el Registro Único Tributario (RUT).

Extrae únicamente la información solicitada.

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

INSTRUCCIONES:

- El NIT debe corresponder al número de identificación tributaria
  de la persona jurídica.
- La razón social debe corresponder exactamente al nombre de la empresa.
- La dirección debe corresponder a la dirección principal registrada.
- No inventes información.
- Si un dato no aparece claramente, utiliza null.
- No agregues campos adicionales.

Contenido:

{texto}
""",


    # =============================================
    # DUTA
    # =============================================

    "DUTA": """
Eres un analista documental experto en operaciones aduaneras
y Zona Franca en Colombia.

Analiza el Documento Único de Tránsito Aduanero (DUTA).

Responde exclusivamente un JSON válido.

{{
    "tipo_documento": "DUTA",
    "numero_documento": null,
    "destinatario": null,
    "usuario_zona_franca": null,
    "incoterm": null,
    "moneda": null,
    "numero_factura_comercial": null,
    "valor_factura": null,
    "valor_fob_usd": null,
    "valor_cif_usd": null,
    "peso_bruto": null,
    "peso_neto": null
}}

INSTRUCCIONES IMPORTANTES:

1. numero_documento:
   Extrae el número principal del DUTA.

2. destinatario:
   Extrae el consignatario, destinatario o importador,
   según aparezca claramente identificado en el documento.

3. usuario_zona_franca:
   Extrae únicamente el Usuario Calificado de Zona Franca,
   Usuario Industrial o Usuario Operador identificado
   como tal en el documento.

4. numero_factura_comercial:
   Busca específicamente el número asociado a un documento
   identificado como FACTURA COMERCIAL.

5. valor_factura:
   Extrae únicamente el valor que esté expresamente asociado
   a la factura comercial identificada como documento soporte.

   NO utilices el valor FOB.
   NO utilices el valor CIF.
   NO utilices valores estadísticos totales.
   NO confundas valores de transporte con el valor de factura.

6. valor_fob_usd:
   Extrae el valor FOB total si aparece.

7. valor_cif_usd:
   Extrae el valor CIF total si aparece.

8. peso_bruto:
   Extrae únicamente el campo expresamente identificado
   como peso bruto.

9. peso_neto:
   Extrae únicamente el campo expresamente identificado
   como peso neto.

REGLA PRINCIPAL:

Si no puedes determinar con seguridad un dato,
devuelve null.

No inventes información.
No agregues campos adicionales.

Contenido:

{texto}
""",


    # =============================================
    # FACTURA COMERCIAL
    # =============================================

    "FACTURA COMERCIAL": """
Eres un analista documental experto en comercio exterior.

Analiza la Factura Comercial proporcionada.

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

INSTRUCCIONES IMPORTANTES:

1. vendedor:
   Corresponde al exportador o proveedor que emite
   la factura comercial.

2. comprador:
   Corresponde al cliente, importador o comprador
   de la mercancía.

3. nit:
   Extrae únicamente el NIT o identificación tributaria
   correspondiente al COMPRADOR.

4. razon_social:
   Extrae la razón social del COMPRADOR.

   Si el nombre aparece acompañado por un nombre comercial,
   sucursal, establecimiento o texto adicional, utiliza
   preferiblemente la razón social legal completa
   del comprador.

5. direccion:
   Extrae la dirección del COMPRADOR.

   No agregues ciudad o país si no forman parte de la dirección
   principal.

6. valor_factura:
   Extrae el TOTAL de la factura comercial.

   No extraigas:
   - valores unitarios,
   - subtotales de líneas,
   - costos de transporte,
   - valores de seguros,
   - valores FOB o CIF provenientes de otro documento.

7. moneda:
   Identifica la moneda del valor total de la factura.

8. incoterm:
   Extrae el Incoterm únicamente si aparece expresamente.

9. descripcion_mercancia:
   Resume brevemente la mercancía facturada.

No inventes información.

Si un dato no aparece claramente, utiliza null.

No agregues campos adicionales.

Contenido:

{texto}
""",


    # =============================================
    # BL
    # =============================================

    "BL": """
Eres un analista documental experto en transporte internacional
y documentos de transporte.

Analiza el Bill of Lading proporcionado.

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

INSTRUCCIONES:

1. numero_bl:
   Extrae el número del Bill of Lading.

2. shipper:
   Extrae el remitente o exportador.

3. consignee:
   Extrae el consignatario o destinatario de la mercancía.

4. notify_party:
   Extrae la parte a notificar.

5. usuario_zona_franca:
   Extrae este valor solamente si aparece expresamente
   identificado como Usuario Industrial, Usuario Calificado
   o Usuario de Zona Franca.

   No confundas el consignatario con el Usuario de Zona Franca.

6. peso_bruto:
   Extrae únicamente el peso expresamente identificado
   como Gross Weight o Peso Bruto.

7. peso_neto:
   Extrae únicamente el peso expresamente identificado
   como Net Weight o Peso Neto.

Si no puedes identificar con seguridad un valor,
utiliza null.

No inventes información.
No agregues campos adicionales.

Contenido:

{texto}
""",


    # =============================================
    # PACKING LIST
    # =============================================

    "PACKING LIST": """
Eres un analista documental experto en documentos
de comercio exterior.

Analiza el Packing List proporcionado.

Responde exclusivamente un JSON válido.

{{
    "tipo_documento": "PACKING LIST",
    "numero_documento": null,
    "peso_bruto": null,
    "peso_neto": null,
    "cantidad_bultos": null
}}

INSTRUCCIONES:

- peso_bruto debe corresponder únicamente al Gross Weight.
- peso_neto debe corresponder únicamente al Net Weight.
- cantidad_bultos debe corresponder al total de packages,
  packages count o número de bultos.
- No inventes información.
- Si un dato no aparece claramente utiliza null.

No agregues campos adicionales.

Contenido:

{texto}
""",


    # =============================================
    # DOCUMENTO DESCONOCIDO
    # =============================================

    "DOCUMENTO DESCONOCIDO": """
Analiza cuidadosamente el documento PDF proporcionado.

Determina cuál de los siguientes tipos documentales
describe mejor el documento:

- RUT
- DUTA
- FACTURA COMERCIAL
- BL
- PACKING LIST
- CERTIFICADO DE FLETES
- DOCUMENTO DESCONOCIDO

Responde exclusivamente un JSON válido
con esta estructura:

{{
    "tipo_documento": "NOMBRE DEL TIPO"
}}

INSTRUCCIONES:

- Analiza el contenido visual y textual completo del PDF.
- No inventes información.
- Selecciona únicamente uno de los tipos indicados.
- Si no puedes identificarlo con seguridad utiliza
  DOCUMENTO DESCONOCIDO.
"""
}


# -------------------------------------------------
# LIMPIAR RESPUESTA DE GEMINI
# -------------------------------------------------

def limpiar_respuesta(respuesta):

    texto_json = respuesta.text.strip()

    texto_json = (
        texto_json
        .replace("```json", "")
        .replace("```JSON", "")
        .replace("```", "")
        .strip()
    )

    return json.loads(texto_json)


# -------------------------------------------------
# EXTRAER DATOS DESDE TEXTO
# -------------------------------------------------

def extraer_datos(tipo_documento, texto):

    prompt = PROMPTS.get(
        tipo_documento,
        PROMPTS["DOCUMENTO DESCONOCIDO"]
    )

    # DOCUMENTO DESCONOCIDO no contiene {texto}
    # porque se utiliza principalmente con PDF directo.
    if "{texto}" in prompt:

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
            "error": "Gemini no devolvió un JSON válido."
        }

    except Exception as e:

        return {
            "error": f"Error extrayendo datos: {str(e)}"
        }


# -------------------------------------------------
# ANALIZAR PDF DIRECTAMENTE CON GEMINI
# -------------------------------------------------

def analizar_pdf_con_gemini(
    ruta_pdf,
    tipo_documento="DOCUMENTO DESCONOCIDO"
):

    archivo_gemini = None

    try:

        print(
            "Enviando PDF directamente a Gemini..."
        )

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

    except json.JSONDecodeError:

        return {
            "error": (
                "Gemini no devolvió un JSON válido "
                "al analizar el PDF."
            )
        }

    except Exception as e:

        return {
            "error": (
                f"Error analizando PDF con Gemini: {str(e)}"
            )
        }

    finally:

        if archivo_gemini:

            try:

                client.files.delete(
                    name=archivo_gemini.name
                )

            except Exception:

                pass
