import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

for sid in [3539, 3550, 3600, 3650, 3700, 3750, 3800]:
    r = requests.get(f"https://www.senado.gob.mx/informacion/diario/sesion/{sid}", headers=headers, verify=False, timeout=15)
    soup = BeautifulSoup(r.text, "html.parser")
    gaceta = soup.find("div", id="gaceta")
    panel_body = gaceta.find("div", class_="panel-body") if gaceta else None
    body_rows = panel_body.find_all("div", class_="row", recursive=False) if panel_body else []
    meta = body_rows[2].get_text(" | ", strip=True) if len(body_rows) > 2 else ""
    date_txt = body_rows[3].get_text(" | ", strip=True) if len(body_rows) > 3 else ""
    print(f"sid={sid}: len={len(r.text)} | meta={meta} | date={date_txt}")

