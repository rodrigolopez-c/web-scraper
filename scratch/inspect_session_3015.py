import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

for sid in ["3015", "3100", "3278", "3400"]:
    u = f"https://www.senado.gob.mx/informacion/diario/sesion/{sid}"
    r = requests.get(u, headers=headers, verify=False, timeout=20)
    print(f"Session {sid}: status={r.status_code}, len={len(r.text)}")
    with open(f"scratch/senado_{sid}.html", "w", encoding="utf-8") as f:
        f.write(r.text)

