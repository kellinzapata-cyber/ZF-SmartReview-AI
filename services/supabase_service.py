import os
import streamlit as st
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Intentar leer primero los Secrets de Streamlit
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    # Respaldo para ejecución local con archivo .env
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")


if not SUPABASE_URL:
    raise ValueError(
        "No se encontró SUPABASE_URL en la configuración."
    )

if not SUPABASE_KEY:
    raise ValueError(
        "No se encontró SUPABASE_KEY en la configuración."
    )


# Diagnóstico seguro: NO muestra la clave
print("SUPABASE_URL encontrada:", bool(SUPABASE_URL))

if SUPABASE_KEY.startswith("sb_secret_"):
    print("Tipo de clave Supabase: SECRET KEY")
elif SUPABASE_KEY.startswith("sb_publishable_"):
    print("Tipo de clave Supabase: PUBLISHABLE KEY")
else:
    print("Tipo de clave Supabase: LEGACY O DESCONOCIDA")


supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
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
