import requests
import pypdfium2 as pdfium
import urllib3
import re
import html
import unicodedata

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Let's download a sample PDF
sample_pdf_url = "https://infolej.congresojal.gob.mx/documentos/Sesion/Diario 1-JP25Oct21.pdf"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

print(f"Downloading sample PDF: {sample_pdf_url}")
r = requests.get(sample_pdf_url, headers=headers, verify=False, timeout=30)
print(f"Status: {r.status_code}, Bytes: {len(r.content)}")

pdf = pdfium.PdfDocument(r.content)
print(f"Total pages: {len(pdf)}")

pages_text = []
for i in range(min(5, len(pdf))): # first 5 pages
    page = pdf[i]
    textpage = page.get_textpage()
    txt = textpage.get_text_range()
    pages_text.append(f"--- PAGE {i+1} ---\n" + txt)

sample_text = "\n\n".join(pages_text)
print("\n--- SAMPLE EXTRACTED TEXT (FIRST 5 PAGES) ---")
print(sample_text[:1500])
