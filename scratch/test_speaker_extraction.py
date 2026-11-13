import requests
from bs4 import BeautifulSoup
import urllib3
import re
import html
import unicodedata
from urllib.parse import urljoin
import pypdfium2 as pdfium

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://infolej.congresojal.gob.mx/consulta/DiarioDeDebates.php"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

def get_sample_per_leg():
    session = requests.Session()
    samples = []
    
    for leg in ['LX', 'LXI', 'LXII', 'LXIII', 'LXIV']:
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
        text = html.unescape(r.content.decode('iso-8859-1', errors='replace'))
        soup = BeautifulSoup(text, 'html.parser')
        
        tables = soup.find_all('table')
        leg_samples = []
        for t in tables:
            a = t.find('a', href=True)
            if a and '.pdf' in a['href'].lower():
                row_text = t.get_text(' ', strip=True).replace('Acceder', '').strip()
                date_match = re.search(r'd[íi]a\s*(\d{2}-\d{2}-\d{4})', row_text, re.IGNORECASE)
                date_str = date_match.group(1) if date_match else ""
                
                leg_samples.append({
                    'legislatura': leg,
                    'title': row_text,
                    'date': date_str,
                    'pdf_url': urljoin(BASE_URL, a['href'])
                })
                if len(leg_samples) >= 3:
                    break
        samples.extend(leg_samples)
    return samples

def extract_speaker(raw_text: str):
    header = raw_text[:2500]
    
    # Try various patterns
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
            # Check length sanity
            if 4 <= len(val) <= 50 and not any(k in val.lower() for k in ['general', 'proceso', 'coordinador', 'tabla', 'pagina', 'secretaria']):
                if not val.lower().startswith('dip'):
                    val = f"Dip. {val}"
                return val
                
    return "Mesa Directiva del H. Congreso del Estado de Jalisco"

def main():
    samples = get_sample_per_leg()
    print(f"Testing speaker extraction on {len(samples)} samples...")
    for idx, s in enumerate(samples, 1):
        try:
            r = requests.get(s['pdf_url'], headers=HEADERS, verify=False, timeout=20)
            pdf = pdfium.PdfDocument(r.content)
            txt = pdf[0].get_textpage().get_text_range()
            try:
                txt_latin = txt.encode('latin-1', errors='ignore').decode('latin-1')
                if '\ufffd' not in txt_latin:
                    txt = txt_latin
                else:
                    txt = txt.encode('latin-1', errors='ignore').decode('utf-8', errors='replace')
            except Exception:
                pass
            
            speaker = extract_speaker(txt)
            print(f"[{s['legislatura']}] Date: {s['date']} | Speaker: '{speaker}' | Title: {s['title'][:45]}")
        except Exception as e:
            print(f"Error processing {s['pdf_url']}: {e}")

if __name__ == "__main__":
    main()
