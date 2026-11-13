import requests
from bs4 import BeautifulSoup
import urllib3
import re

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

session = requests.Session()
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
url = 'https://infolej.congresojal.gob.mx/consulta/DiarioDeDebates.php'

data = {
    'C_Legis': 'LXIII',
    'C_NS': '0',
    'C_tipo': '0',
    'C_Fecha': '',
    'C_Fecha1': '',
    'C_Acuerdo': '0',
    'C_buscar': '1',
    'Submit': 'Buscar'
}
r = session.post(url, headers=headers, data=data, verify=False)
soup = BeautifulSoup(r.text, 'html.parser')

tables = soup.find_all('table')
print(f"Total tables: {len(tables)}")
count = 0
for idx, t in enumerate(tables):
    a = t.find('a', href=True)
    if a and '.pdf' in a['href'].lower():
        row_text = t.get_text(' ', strip=True)
        print(f"Item {count}: Text='{row_text}' | Href='{a['href']}'")
        count += 1
        if count >= 10:
            break
