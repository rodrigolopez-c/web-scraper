import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

for sid in range(3750, 3780):
    r = requests.get(f"https://www.senado.gob.mx/informacion/diario/sesion/{sid}", headers=headers, verify=False, timeout=15)
    if len(r.text) > 15000:
        soup = BeautifulSoup(r.text, "html.parser")
        gaceta = soup.find("div", id="gaceta")
        panel_body = gaceta.find("div", class_="panel-body") if gaceta else None
        body_rows = panel_body.find_all("div", class_="row", recursive=False) if panel_body else []
        date_txt = body_rows[3].get_text(" | ", strip=True) if len(body_rows) > 3 else ""
        print(f"sid={sid}: len={len(r.text)} | {date_txt}")
    else:
        print(f"sid={sid}: EMPTY (len={len(r.text)})")

