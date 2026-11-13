import requests
from bs4 import BeautifulSoup
import urllib3
import re
import html
import unicodedata
from urllib.parse import urljoin
import pypdfium2 as pdfium
from concurrent.futures import ThreadPoolExecutor
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://infolej.congresojal.gob.mx/consulta/DiarioDeDebates.php"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

def fetch_session_list():
    session = requests.Session()
    items = []
    
    legislaturas = ['LX', 'LXI', 'LXII', 'LXIII', 'LXIV']
    for leg in legislaturas:
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
        r = session.post(BASE_URL, headers=HEADERS, data=data, verify=False, timeout=15)
        text = r.content.decode('iso-8859-1', errors='replace')
        text = html.unescape(text)
        soup = BeautifulSoup(text, 'html.parser')
        
        tables = soup.find_all('table')
        for t in tables:
            a = t.find('a', href=True)
            if a and '.pdf' in a['href'].lower():
                row_text = t.get_text(' ', strip=True)
                # Clean up "Acceder"
                row_text = row_text.replace('Acceder', '').strip()
                
                # Parse number
                num_match = re.search(r'n[úu]mero\s*(\d+)', row_text, re.IGNORECASE)
                num_sesion = num_match.group(1) if num_match else ""
                
                # Parse date
                date_match = re.search(r'd[íi]a\s*(\d{2}-\d{2}-\d{4})', row_text, re.IGNORECASE)
                date_str = date_match.group(1) if date_match else ""
                
                # Parse type
                type_match = re.search(r'(Junta Preparatoria|Extraordinaria de Responsabilidades|Extraordinaria|Ordinaria|Solemne)', row_text, re.IGNORECASE)
                tipo_str = type_match.group(1) if type_match else "Sesión Plenaria"
                
                full_pdf_url = urljoin(BASE_URL, a['href'])
                
                items.append({
                    'legislatura': leg,
                    'num_sesion': num_sesion,
                    'tipo_sesion': tipo_str,
                    'fecha': date_str,
                    'title_raw': row_text,
                    'pdf_url': full_pdf_url
                })
                
    print(f"Total sessions collected: {len(items)}")
    return items

def process_item(item, idx):
    item_id = f"DD-{item['legislatura']}-{idx:03d}"
    
    # Download PDF
    try:
        r = requests.get(item['pdf_url'], headers=HEADERS, verify=False, timeout=25)
        content_bytes = r.content
    except Exception as e:
        print(f"Error fetching PDF {item_id}: {e}")
        return None

    # Extract text with pypdfium2
    raw_text = ""
    try:
        pdf = pdfium.PdfDocument(content_bytes)
        pages_text = []
        for p in pdf:
            txt = p.get_textpage().get_text_range()
            # Fix PDF encoding
            try:
                txt_latin = txt.encode('latin-1', errors='ignore').decode('latin-1')
                if '\ufffd' not in txt_latin:
                    txt = txt_latin
                else:
                    txt = txt.encode('latin-1', errors='ignore').decode('utf-8', errors='replace')
            except Exception:
                pass
            pages_text.append(txt)
        raw_text = "\n\n".join(pages_text)
    except Exception as pdf_err:
        print(f"PDF extraction error for {item_id}: {pdf_err}")
        return None

    # Clean text
    clean_text = clean_discurso_text(raw_text)
    
    # Resolve speaker & role
    speaker, role = extract_speaker_role(raw_text, item['legislatura'])
    
    context = f"{item['title_raw']} - {item['legislatura']} Legislatura del H. Congreso del Estado de Jalisco"
    
    return {
        'id': item_id,
        'language': 'es',
        'speaker': speaker,
        'role': role,
        'date': item['fecha'],
        'context': context,
        'text-original': raw_text,
        'text_clean': clean_text
    }

def clean_discurso_text(text: str) -> str:
    if not text:
        return ""
    
    text = unicodedata.normalize('NFC', text)
    text = text.replace('\xad', '').replace('\xa0', ' ').replace('\ufeff', '').replace('\u200b', '')
    
    # Strip header lines like "Año I · Tomo I · Núm. 1 2 Guadalajara, Jalisco..."
    text = re.sub(r'A[ñn]o\s+[I|V|X]+\s*[\u2022\u00b7\-•]?\s*Tomo\s+[I|V|X]+.*?\n', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Guadalajara,\s*Jalisco,\s*\d{1,2}\s+de\s+[a-z]+\s+de\s+\d{4}', '', text, flags=re.IGNORECASE)
    
    # Strip isolated page numbers at start/end of lines
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
    
    # Remove soft hyphen line breaks ('institu-\ncional' -> 'institucional')
    text = re.sub(r'([a-zA-ZáéíóúñÁÉÍÓÚÑ]{2,})-\s*\n\s*([a-zA-ZáéíóúñÁÉÍÓÚÑ]{2,})', r'\1\2', text)
    
    # Normalize multiple whitespace and newlines
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

def extract_speaker_role(raw_text: str, legislatura: str):
    # Extract Presidencia from page 1 text
    pres_match = re.search(r'Presidencia:\s*(?:C\.\s*)?(?:Diputad[oa]\s*)?([A-ZÁÉÍÓÚÑa-záéíóúñ\s\.]+?)(?=\.|\n|Secretar|\n\n)', raw_text[:2000], re.IGNORECASE)
    if not pres_match:
        pres_match = re.search(r'Dip\.\s*([A-ZÁÉÍÓÚÑa-záéíóúñ\s\.]+?)\s*\n\s*Presidente', raw_text[:2000], re.IGNORECASE)
        
    speaker = pres_match.group(1).strip() if pres_match else "Mesa Directiva"
    # Clean speaker text
    speaker = re.sub(r'\s+', ' ', speaker).strip(' .')
    if len(speaker) > 60 or len(speaker) < 4:
        speaker = "Mesa Directiva del H. Congreso de Jalisco"
        
    role = f"Presidente de la Mesa Directiva / {legislatura} Legislatura del H. Congreso del Estado de Jalisco"
    return speaker, role

if __name__ == "__main__":
    t0 = time.time()
    items = fetch_session_list()
    print(f"Sample test processing first 5 items...")
    results = []
    for idx, item in enumerate(items[:5], 1):
        res = process_item(item, idx)
        if res:
            results.append(res)
            print(f"[{res['id']}] Date: {res['date']} | Speaker: {res['speaker']} | Clean text len: {len(res['text_clean'])}")
    print(f"Completed in {time.time()-t0:.2f}s")
