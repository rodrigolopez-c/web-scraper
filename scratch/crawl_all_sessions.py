import requests
from bs4 import BeautifulSoup
import urllib3
import re
from urllib.parse import urljoin

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://infolej.congresojal.gob.mx/consulta/DiarioDeDebates.php"

def crawl_all():
    session = requests.Session()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    # First GET to check options
    r = session.get(BASE_URL, headers=headers, verify=False)
    soup = BeautifulSoup(r.text, 'html.parser')
    leg_select = soup.find('select', {'name': 'C_Legis'})
    legislaturas = []
    if leg_select:
        for opt in leg_select.find_all('option'):
            val = opt.get('value', '').strip()
            if val and val != '0':
                legislaturas.append(val)
                
    print("Found Legislaturas:", legislaturas)
    
    total_pdf_items = []
    
    # Also test empty search (all legislaturas)
    r_all = session.post(BASE_URL, headers=headers, data={'Submit': 'Buscar'}, verify=False)
    soup_all = BeautifulSoup(r_all.text, 'html.parser')
    all_links = soup_all.find_all('a', href=True)
    print(f"Empty search returned {len(all_links)} links")
    
    for leg in legislaturas:
        data = {
            'C_Legis': leg,
            'Submit': 'Buscar'
        }
        res = session.post(BASE_URL, headers=headers, data=data, verify=False)
        soup_leg = BeautifulSoup(res.text, 'html.parser')
        
        # Each result table has session info and link
        # Find all <a> tags with href ending in .pdf or inside tables
        anchors = soup_leg.find_all('a', href=True)
        pdf_count = 0
        for a in anchors:
            href = a['href']
            if '.pdf' in href.lower() or 'documentos/Sesion' in href:
                full_pdf_url = urljoin(BASE_URL, href)
                # Find parent table or container text for metadata
                parent = a.find_parent('table') or a.find_parent('tr') or a.parent
                row_text = parent.get_text(" ", strip=True) if parent else ""
                total_pdf_items.append({
                    'legislatura': leg,
                    'text': row_text,
                    'pdf_url': full_pdf_url,
                    'relative_url': href
                })
                pdf_count += 1
        print(f"Legislatura {leg}: found {pdf_count} PDFs")

    print(f"\nTotal PDF items collected across all legislaturas: {len(total_pdf_items)}")
    if total_pdf_items:
        print("Sample item:", total_pdf_items[0])

if __name__ == "__main__":
    crawl_all()
