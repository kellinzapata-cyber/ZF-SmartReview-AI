import fitz  # PyMuPDF


def leer_pdf(ruta_pdf):

    texto = ""

    documento = fitz.open(ruta_pdf)

    for pagina in documento:
        texto += pagina.get_text()

    documento.close()

    return texto