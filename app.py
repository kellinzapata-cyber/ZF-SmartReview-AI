import streamlit as st
from pathlib import Path
import shutil

from main import procesar_expediente

st.set_page_config(
    page_title="ZF SmartReview AI",
    page_icon="📄",
    layout="wide"
)

st.title("📄 ZF SmartReview AI")
st.caption("Sistema inteligente de revisión documental para operaciones de Zona Franca")

st.write("""
Este sistema utiliza **Google AI Studio (Gemini)** para:

- Clasificar documentos
- Extraer información relevante
- Validar consistencia documental
- Guardar resultados en Supabase
""")

st.divider()

uploaded_files = st.file_uploader(
    "Seleccione los documentos del expediente",
    type="pdf",
    accept_multiple_files=True
)

if uploaded_files:

    carpeta = Path("temp_uploads")

    carpeta.mkdir(exist_ok=True)

   
    # Limpiar carpeta temporal
    for archivo in carpeta.glob("*"):
        if archivo.is_file():
            archivo.unlink(missing_ok=True)

    # guardar archivos cargados
    for archivo in uploaded_files:

        destino = carpeta / archivo.name

        with open(destino, "wb") as f:
            f.write(archivo.getbuffer())

    st.success(f"{len(uploaded_files)} documento(s) cargado(s).")

    st.write("### Documentos")

    for archivo in uploaded_files:
        st.write(f"📄 {archivo.name}")

    if st.button("🚀 Procesar expediente"):

        with st.spinner("Analizando documentos con Google AI Studio..."):

            documentos, validaciones = procesar_expediente("temp_uploads")

        st.success("Proceso terminado correctamente.")

        ok = sum(1 for v in validaciones if v["estado"] == "OK")
        errores = sum(1 for v in validaciones if v["estado"] == "ERROR")
        pendientes = len(validaciones) - ok - errores

        c1, c2, c3 = st.columns(3)

        c1.metric("📄 Documentos", len(documentos))
        c2.metric("✅ Correctas", ok)
        c3.metric("⚠ Pendientes", pendientes)

        st.divider()

        st.subheader("Resultado de las validaciones")

        for v in validaciones:

            estado = v.get("estado","")

            texto = f"""
**Validación:** {v.get('validacion')}

**Estado:** {estado}

**Documento 1:** {v.get('valor_1','')}

**Documento 2:** {v.get('valor_2','')}
"""

            if estado == "OK":
                st.success(texto)

            elif estado == "ERROR":
                st.error(texto)

            else:
                st.warning(texto)
