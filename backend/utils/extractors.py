import fitz  # Correct import for PyMuPDF
import docx  # This should now work correctly


# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    document = fitz.open(pdf_path)
    text = ""
    for page in document:
        text += page.get_text()
    return text


# Function to extract text from DOCX
def extract_text_from_docx(docx_path):
    doc = docx.Document(docx_path)
    text = ""
    for para in doc.paragraphs:
        text += (
            para.text.strip() + "\n"
        )  # Strip unnecessary spaces and add a new line after each paragraph.
    return text
