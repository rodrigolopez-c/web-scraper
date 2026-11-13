import os
import re
import csv
import json
import time
import html
import logging
import threading
import unicodedata
from urllib.parse import urljoin, urlparse, urlunparse, quote
import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import pypdfium2 as pdfium
import trafilatura
from newspaper import Article, Config
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3_logger = logging.getLogger('urllib3')
urllib3_logger.setLevel(logging.CRITICAL)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

BASE_DIR = r"c:\Users\PC\OneDrive - ITESO\Iteso\11vo semestre\PAP II\Proyectos\scrapping"
BASE_URL = "https://infolej.congresojal.gob.mx/consulta/DiarioDeDebates.php"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
LEGISLATURAS = ['LX', 'LXI', 'LXII', 'LXIII', 'LXIV']

PDF_LOCK = threading.Lock()

def sanitize_url(url: str) -> str:
    parsed = urlparse(url)
    encoded_path = quote(parsed.path)
    return urlunparse((parsed.scheme, parsed.netloc, encoded_path, parsed.params, parsed.query, parsed.fragment))

def fetch_all_sessions():
    session = requests.Session()
    items = []
    logging.info("Fetching session list for all Legislaturas (LX to LXIV)...")
    
    for leg in LEGISLATURAS:
        data = {
            'C_Legis': leg,
            'C_NS': '0',
            'C_tipo': '0',
            'C_Fecha': '',
            'C_Fecha1': '',
            'C_Acuerdo': '0',
            'C_buscar': '1',
            'Submit': 'Buscar'
        }
        try:
            r = session.post(BASE_URL, headers=HEADERS, data=data, verify=False, timeout=20)
            text = html.unescape(r.content.decode('iso-8859-1', errors='replace'))
            soup = BeautifulSoup(text, 'html.parser')
            
            tables = soup.find_all('table')
            count = 0
            for t in tables:
                a = t.find('a', href=True)
                if a and '.pdf' in a['href'].lower():
                    row_text = t.get_text(' ', strip=True).replace('Acceder', '').strip()
                    
                    num_match = re.search(r'n[úu]mero\s*(\d+)', row_text, re.IGNORECASE)
                    num_sesion = num_match.group(1) if num_match else f"{count+1}"
                    
                    date_match = re.search(r'd[íi]a\s*(\d{2}-\d{2}-\d{4})', row_text, re.IGNORECASE)
                    date_str = date_match.group(1) if date_match else ""
                    
                    type_match = re.search(r'(Junta Preparatoria|Extraordinaria de Responsabilidades|Extraordinaria|Ordinaria|Solemne)', row_text, re.IGNORECASE)
                    tipo_str = type_match.group(1) if type_match else "Sesión Plenaria"
                    
                    raw_pdf_url = urljoin(BASE_URL, a['href'])
                    clean_pdf_url = sanitize_url(raw_pdf_url)
                    count += 1
                    
                    items.append({
                        'legislatura': leg,
                        'num_sesion': num_sesion,
                        'tipo_sesion': tipo_str,
                        'fecha': date_str,
                        'title_raw': row_text,
                        'pdf_url': clean_pdf_url,
                        'leg_index': count
                    })
            logging.info(f"Legislatura {leg}: found {count} sessions.")
        except Exception as e:
            logging.error(f"Error fetching Legislatura {leg}: {e}")
            
    logging.info(f"Total sessions cataloged across all Legislaturas: {len(items)}")
    return items

def extract_pdf_raw_text(pdf_bytes: bytes) -> str:
    if not pdf_bytes or not pdf_bytes.startswith(b'%PDF'):
        return ""
    try:
        with PDF_LOCK:
            pdf = pdfium.PdfDocument(pdf_bytes)
            pages_text = []
            for page in pdf:
                txt = page.get_textpage().get_text_range()
                try:
                    txt_latin = txt.encode('latin-1', errors='ignore').decode('latin-1')
                    if '\ufffd' not in txt_latin:
                        txt = txt_latin
                    else:
                        txt = txt.encode('latin-1', errors='ignore').decode('utf-8', errors='replace')
                except Exception:
                    pass
                pages_text.append(txt)
        return "\n\n".join(pages_text)
    except Exception as e:
        logging.warning(f"pypdfium2 extraction failed: {e}")
        return ""

def clean_text_common(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize('NFC', text)
    text = text.replace('\xad', '').replace('\xa0', ' ').replace('\ufeff', '').replace('\u200b', '')
    
    text = re.sub(r'A[ñn]o\s+[I|V|X]+\s*[\u2022\u00b7\-•]?\s*Tomo\s+[I|V|X]+.*?\n', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Guadalajara,\s*Jalisco,\s*\d{1,2}\s+de\s+[a-z]+\s+de\s+\d{4}', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'([a-zA-ZáéíóúñÁÉÍÓÚÑ]{2,})-\s*\n\s*([a-zA-ZáéíóúñÁÉÍÓÚÑ]{2,})', r'\1\2', text)
    
    lines = [line.strip() for line in text.split('\n')]
    cleaned_lines = []
    blank_count = 0
    for l in lines:
        if not l:
            blank_count += 1
            if blank_count <= 2:
                cleaned_lines.append('')
        else:
            blank_count = 0
            cleaned_lines.append(l)
    return '\n'.join(cleaned_lines).strip()

def extract_speaker(raw_text: str):
    header = raw_text[:3000]
    patterns = [
        r'Presidencia:\s*(?:C\.\s*)?(?:Diputad[oa]\s*)?([A-ZÁÉÍÓÚÑa-záéíóúñ\s\.\-–]+?)(?=\.|\n|Secretar|\n\n)',
        r'(?:C\.\s*)?Diputad[oa]\s+([A-ZÁÉÍÓÚÑa-záéíóúñ\s\.]+?)\s*\n\s*Presidente',
        r'Presidente:\s*(?:C\.\s*)?(?:Diputad[oa]\s*)?([A-ZÁÉÍÓÚÑa-záéíóúñ\s\.]+?)(?=\.|\n|\n\n)',
        r'Presidida por el diputad[oa]\s+([A-ZÁÉÍÓÚÑa-záéíóúñ\s\.]+?)(?=\.|\n|,\s*presidente)',
        r'Dip\.\s*([A-ZÁÉÍÓÚÑa-záéíóúñ\s\.]+?)\s*\n\s*Presidente'
    ]
    for pat in patterns:
        m = re.search(pat, header, re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            val = re.sub(r'\s+', ' ', val).strip(' .')
            if 4 <= len(val) <= 50 and not any(k in val.lower() for k in ['general', 'proceso', 'coordinador', 'tabla', 'pagina', 'secretaria']):
                if not val.lower().startswith('dip'):
                    val = f"Dip. {val}"
                return val
    return "Mesa Directiva del H. Congreso del Estado de Jalisco"

def process_item_full(item):
    item_id = f"DD-{item['legislatura']}-{item['leg_index']:03d}"
    try:
        r = requests.get(item['pdf_url'], headers=HEADERS, verify=False, timeout=30)
        if r.status_code != 200 or not r.content.startswith(b'%PDF'):
            return None
        pdf_bytes = r.content
    except Exception as e:
        logging.error(f"Failed download {item_id}: {e}")
        return None

    raw_text = extract_pdf_raw_text(pdf_bytes)
    if not raw_text:
        return None

    speaker = extract_speaker(raw_text)
    role = f"Presidente de la Mesa Directiva / {item['legislatura']} Legislatura del H. Congreso del Estado de Jalisco"
    context = f"{item['title_raw']} - {item['legislatura']} Legislatura del H. Congreso del Estado de Jalisco"
    
    clean_base = clean_text_common(raw_text)
    
    # Trafilatura
    traf_extracted = trafilatura.extract(raw_text) if raw_text else ""
    clean_trafilatura = clean_text_common(traf_extracted if traf_extracted else clean_base)
    
    # Newspaper3k
    news_article = Article(url=item['pdf_url'])
    news_article.set_html(f"<html><body><h1>{context}</h1><p>{clean_base}</p></body></html>")
    try:
        news_article.parse()
        news_text = news_article.text
    except Exception:
        news_text = clean_base
    clean_newspaper = clean_text_common(news_text if news_text else clean_base)
    
    clean_playwright = clean_base

    date_formatted = item['fecha']
    if date_formatted and len(date_formatted) == 10 and '-' in date_formatted:
        parts = date_formatted.split('-')
        if len(parts[0]) == 2 and len(parts[2]) == 4:
            date_formatted = f"{parts[2]}-{parts[1]}-{parts[0]}"

    base_record = {
        'id': item_id,
        'language': 'es',
        'speaker': speaker,
        'role': role,
        'date': date_formatted,
        'context': context,
        'text-original': raw_text
    }

    rec_universal = dict(base_record, text_clean=clean_base)
    rec_trafilatura = dict(base_record, text_clean=clean_trafilatura)
    rec_newspaper = dict(base_record, text_clean=clean_newspaper)
    rec_playwright = dict(base_record, text_clean=clean_playwright)

    return rec_universal, rec_trafilatura, rec_newspaper, rec_playwright

if __name__ == "__main__":
    t0 = time.time()
    items = fetch_all_sessions()
    
    logging.info(f"Processing {len(items)} sessions with ThreadPoolExecutor...")
    
    list_universal = []
    list_trafilatura = []
    list_newspaper = []
    list_playwright = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(process_item_full, items))

    for res in results:
        if res:
            u, t, n, p = res
            list_universal.append(u)
            list_trafilatura.append(t)
            list_newspaper.append(n)
            list_playwright.append(p)

    logging.info(f"Successfully processed {len(list_universal)} sessions in {time.time()-t0:.2f}s.")

    columns = ['id', 'language', 'speaker', 'role', 'date', 'context', 'text-original', 'text_clean']

    def save_dataset(data, name):
        df = pd.DataFrame(data)[columns]
        xlsx_path = os.path.join(BASE_DIR, f"{name}.xlsx")
        csv_path = os.path.join(BASE_DIR, f"{name}.csv")
        df.to_excel(xlsx_path, index=False)
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        logging.info(f"SAVED: {xlsx_path} and {csv_path} ({len(df)} rows)")

    save_dataset(list_universal, "diario_debates")
    save_dataset(list_trafilatura, "diario_debates_trafilatura")
    save_dataset(list_newspaper, "diario_debates_newspaper")
    save_dataset(list_playwright, "diario_debates_playwright")
    
    print("\nDataset generation completed successfully!")
