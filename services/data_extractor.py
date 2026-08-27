import os
import json
import re

from dotenv import load_dotenv
from google import genai


# =========================================================
# CONFIGURACIÓN
# =========================================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError(
        "ERROR: No se encontró GEMINI_API_KEY. "
        "Verifica la configuración de Secrets de Streamlit."
    )


client = genai.Client(
    api_key=API_KEY
)


MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.5-flash-lite"
)


# =========================================================
# PROMPTS
# =========================================================

PROMPTS = {

    # =====================================================
    # RUT
    # =====================================================

    "RUT": """
Eres un analista documental experto en documentos tributarios colombianos.

Analiza exclusivamente el contenido del siguiente Registro Único Tributario (RUT).

Extrae únicamente la información solicitada.

IMPORTANTE:

- No inventes información.
- No modifiques los números del NIT.
- Si el NIT tiene dígito de verificación separado por guion, consérvalo.
- No confundas el NIT con otros números del documento.
- La razón social debe corresponder al nombre oficial registrado.
- La dirección debe corresponder a la dirección registrada en el RUT.
- Si un dato no aparece claramente, responde null.
- Responde exclusivamente JSON válido.
- No agregues explicaciones.
- No uses bloques de código Markdown.

Estructura obligatoria:

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

Contenido del documento:

{texto}
""",


    # =====================================================
    # DUTA
    # =====================================================

    "DUTA": """
Eres un analista documental experto en operaciones aduaneras y Zona Franca en Colombia.

Analiza exclusivamente el siguiente Documento Único de Tránsito Aduanero (DUTA).

Extrae únicamente los datos solicitados.

IMPORTANTE:

- No inventes información.
- "destinatario" corresponde al consignatario o destinatario final de la mercancía.
- "usuario_zona_franca" corresponde al Usuario Industrial o Usuario de Zona Franca mencionado en el documento.
- "valor_factura" debe corresponder al VALOR TOTAL DE LA FACTURA o valor comercial total relacionado con la operación.
- No extraigas el valor de una sola mercancía, línea o ítem cuando exista un valor total.
- "peso_bruto" debe corresponder al peso bruto total.
- "peso_neto" debe corresponder al peso neto total.
- Conserva los valores numéricos tal como aparecen en el documento.
- Si existen varios pesos, selecciona únicamente el que esté claramente identificado como peso bruto o peso neto.
- Si un dato no aparece claramente, responde null.
- Responde exclusivamente JSON válido.
- No agregues explicaciones.
- No uses bloques de código Markdown.

Estructura obligatoria:

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

Contenido del documento:

{texto}
""",


    # =====================================================
    # FACTURA COMERCIAL
    # =====================================================

    "FACTURA COMERCIAL": """
Eres un analista documental experto en comercio exterior.

Analiza exclusivamente la siguiente Factura Comercial.

Extrae únicamente los datos solicitados.

IMPORTANTE:

- No inventes información.
- "vendedor" corresponde al SELLER, EXPORTER, SUPPLIER o vendedor.
- "comprador" corresponde al BUYER, IMPORTER o comprador.
- "nit" corresponde al NIT del comprador o importador cuando aparezca.
- "razon_social" corresponde a la razón social completa del comprador.
- "direccion" corresponde a la dirección del comprador.
- "incoterm" corresponde al Incoterm expresamente indicado.
- "moneda" corresponde a la moneda de la factura.
- "valor_factura" debe ser el VALOR TOTAL DE LA FACTURA.
- No confundas el valor total con precios unitarios.
- No confundas el valor total con el valor de una línea individual.
- Si aparecen varios valores, selecciona únicamente el identificado como TOTAL INVOICE VALUE, INVOICE TOTAL, GRAND TOTAL, TOTAL AMOUNT o equivalente.
- "descripcion_mercancia" debe ser una descripción general de la mercancía.
- Si un dato no aparece claramente, responde null.
- Responde exclusivamente JSON válido.
- No agregues explicaciones.
- No uses bloques de código Markdown.

Estructura obligatoria:

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

Contenido del documento:

{texto}
""",


    # =====================================================
    # BL
    # =====================================================

    "BL": """
Eres un analista documental experto en transporte internacional y documentos de embarque.

Analiza exclusivamente el siguiente Bill of Lading (BL).

Extrae únicamente los datos solicitados.

IMPORTANTE:

- No inventes información.
- "shipper" corresponde al remitente o exportador.
- "consignee" corresponde al consignatario o destinatario.
- "notify_party" corresponde a la parte que debe ser notificada.
- "usuario_zona_franca" debe extraerse únicamente cuando esté claramente identificado.
- "peso_bruto" debe corresponder al peso bruto total.
- "peso_neto" debe corresponder al peso neto total.
- No confundas cantidad de bultos con peso.
- Si existen varios pesos, utiliza únicamente los valores claramente identificados como peso bruto o neto.
- Si un dato no aparece claramente, responde null.
- Responde exclusivamente JSON válido.
- No agregues explicaciones.
- No uses bloques de código Markdown.

Estructura obligatoria:

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

Contenido del documento:

{texto}
""",


    # =====================================================
    # PACKING LIST
    # =====================================================

    "PACKING LIST": """
Eres un analista documental experto en documentos de comercio exterior.

Analiza exclusivamente el siguiente Packing List o Lista de Empaque.

Extrae únicamente los datos solicitados.

IMPORTANTE:

- No inventes información.
- "peso_bruto" debe ser el peso bruto TOTAL del envío.
- "peso_neto" debe ser el peso neto TOTAL del envío.
- No confundas pesos individuales de productos con el peso total.
- "cantidad_bultos" corresponde al total de paquetes, cajas, pallets, bultos o unidades de embalaje.
- Si un dato no aparece claramente, responde null.
- Responde exclusivamente JSON válido.
- No agregues explicaciones.
- No uses bloques de código Markdown.

Estructura obligatoria:

{{
  "tipo_documento": "PACKING LIST",
  "numero_documento": null,
  "peso_bruto": null,
  "peso_neto": null,
  "cantidad_bultos": null
}}

Contenido del documento:

{texto}
""",


    # =====================================================
    # CERTIFICADO DE FLETES
    # =====================================================

    "CERTIFICADO DE FLETES": """
Eres un analista documental experto en transporte internacional y comercio exterior.

Analiza exclusivamente el siguiente documento de transporte o certificado de fletes.

Determina la información disponible.

IMPORTANTE:

- No inventes información.
- Extrae únicamente información que aparezca claramente en el documento.
- Si un dato no aparece, responde null.
- Responde exclusivamente JSON válido.
- No agregues explicaciones.

Estructura obligatoria:

{{
  "tipo_documento": "CERTIFICADO DE FLETES",
  "numero_documento": null,
  "transportador": null,
  "remitente": null,
  "destinatario": null,
  "valor_flete": null,
  "moneda": null
}}

Contenido del documento:

{texto}
""",


    # =====================================================
    # DOCUMENTO DESCONOCIDO
    # =====================================================

    "DOCUMENTO DESCONOCIDO": """
Eres un experto en clasificación de documentos de comercio exterior y documentos colombianos.

Analiza el siguiente documento.

Determina si corresponde a alguno de estos tipos:

- RUT
- DUTA
- FACTURA COMERCIAL
- BL
- PACKING LIST
- CERTIFICADO DE FLETES

IMPORTANTE:

- No inventes información.
- Si no puedes identificar claramente el documento, utiliza "DOCUMENTO DESCONOCIDO".
- Responde exclusivamente JSON válido.
- No agregues explicaciones.

Estructura obligatoria:

{{
  "tipo_documento": "DOCUMENTO DESCONOCIDO"
}}

Contenido del documento:

{texto}
"""
}


# =========================================================
# LIMPIAR RESPUESTA DE GEMINI
# =========================================================

def limpiar_respuesta(respuesta):

    texto_json = respuesta.text.strip()

    # Eliminar posibles bloques Markdown
    texto_json = texto_json.replace("```json", "")
    texto_json = texto_json.replace("```JSON", "")
    texto_json = texto_json.replace("```", "")
    texto_json = texto_json.strip()

    # Intentar localizar el JSON
    inicio = texto_json.find("{")
    fin = texto_json.rfind("}")

    if inicio != -1 and fin != -1:

        texto_json = texto_json[inicio:fin + 1]

    return json.loads(texto_json)


# =========================================================
# EXTRAER DATOS DESDE TEXTO
# =========================================================

def extraer_datos(tipo_documento, texto):

    # Obtener el prompt correspondiente
    plantilla = PROMPTS.get(
        tipo_documento,
        PROMPTS["DOCUMENTO DESCONOCIDO"]
    )

    # Limitar texto excesivamente grande
    # Se mantiene suficiente contenido para analizar documentos largos
    if texto and len(texto) > 30000:
        texto = texto[:30000]

    # Insertar el contenido del documento
    prompt = plantilla.format(
        texto=texto or ""
    )

    try:

        respuesta = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )

        datos = limpiar_respuesta(respuesta)

        # Verificar que Gemini haya devuelto un diccionario
        if not isinstance(datos, dict):

            return {
                "error": "Gemini devolvió una estructura diferente a un JSON objeto.",
                "respuesta_original": respuesta.text
            }

        # Asegurar que siempre exista tipo_documento
        if "tipo_documento" not in datos:
            datos["tipo_documento"] = tipo_documento

        return datos

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
            "error": f"Error al extraer datos con Gemini: {str(e)}"
        }


# =========================================================
# ANALIZAR PDF DIRECTAMENTE CON GEMINI
# =========================================================

def analizar_pdf_con_gemini(
    ruta_pdf,
    tipo_documento="DOCUMENTO DESCONOCIDO"
):

    """
    Envía directamente el archivo PDF a Gemini.

    Este método es especialmente útil cuando:

    - El PDF está escaneado.
    - PyMuPDF no puede extraer texto.
    - El texto extraído es demasiado corto.
    """

    archivo_gemini = None

    try:

        print("Enviando PDF directamente a Gemini...")

        # Subir archivo a Gemini
        archivo_gemini = client.files.upload(
            file=ruta_pdf
        )

        plantilla = PROMPTS.get(
            tipo_documento,
            PROMPTS["DOCUMENTO DESCONOCIDO"]
        )

        # Para análisis directo del PDF no necesitamos insertar
        # texto extraído. Reemplazamos el marcador.
        prompt = plantilla.format(
            texto="Analiza directamente el contenido visual y textual del PDF adjunto."
        )

        respuesta = client.models.generate_content(
            model=MODEL,
            contents=[
                prompt,
                archivo_gemini
            ]
        )

        datos = limpiar_respuesta(respuesta)

        if not isinstance(datos, dict):

            return {
                "error": "Gemini no devolvió un JSON objeto válido.",
                "respuesta_original": respuesta.text
            }

        if "tipo_documento" not in datos:
            datos["tipo_documento"] = tipo_documento

        return datos

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
            "error": f"Error analizando PDF con Gemini: {str(e)}"
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


# =========================================================
# FUNCIÓN AUXILIAR PARA DETECTAR
# SI EL TEXTO EXTRAÍDO ES INSUFICIENTE
# =========================================================

def texto_insuficiente(texto):

    if texto is None:
        return True

    texto_limpio = re.sub(
        r"\s+",
        "",
        texto
    )

    # Si PyMuPDF extrajo menos de 50 caracteres útiles,
    # probablemente sea un PDF escaneado.
    return len(texto_limpio) < 50
