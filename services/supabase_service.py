import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)


def guardar_documento(documento):

    datos = {
        "archivo": documento.archivo,
        "tipo": documento.tipo,
        "datos": documento.datos
    }

    supabase.table("documentos").insert(datos).execute()


def guardar_validaciones(validaciones):

    for v in validaciones:

        supabase.table("validaciones").insert(v).execute()