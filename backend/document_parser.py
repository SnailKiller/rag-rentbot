# document_parser.py
import io
import pdfplumber
from docx import Document
from PIL import Image
import pytesseract
import os
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"   # 避免 Metal 报错
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"

from typing import List

# If tesseract is not in PATH, you may need to set:
# pytesseract.pytesseract.tesseract_cmd = r"/usr/bin/tesseract"

def parse_pdf(file_bytes: bytes) -> str:
    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            txt = page.extract_text()
            if txt:
                text_parts.append(txt)
            else:
                # fallback: try OCR of page image
                try:
                    im = page.to_image(resolution=150).original
                    ocr_txt = pytesseract.image_to_string(im)
                    text_parts.append(ocr_txt)
                except Exception:
                    pass
    return "\n".join(text_parts)

def parse_docx(file_bytes: bytes) -> str:
    # python-docx requires a path or file-like object
    with io.BytesIO(file_bytes) as f:
        doc = Document(f)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs)

def parse_image(file_bytes: bytes) -> str:
    im = Image.open(io.BytesIO(file_bytes))
    return pytesseract.image_to_string(im)

def parse_file(filename: str, file_bytes: bytes) -> str:
    ext = os.path.splitext(filename.lower())[1]
    if ext == ".pdf":
        return parse_pdf(file_bytes)
    elif ext in [".docx", ".doc"]:
        return parse_docx(file_bytes)
    elif ext in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
        return parse_image(file_bytes)
    else:
        # try as plain text
        try:
            return file_bytes.decode("utf-8")
        except Exception:
            return ""
