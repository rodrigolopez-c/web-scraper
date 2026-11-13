import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

pages = [
    ("LXIV", "I", "https://www.senado.gob.mx/informacion/diario/LXIV/I"),
    ("LXIV", "II", "https://www.senado.gob.mx/informacion/diario/LXIV/II"),
    ("LXIV", "III", "https://www.senado.gob.mx/informacion/diario/LXIV/III"),
    ("LXV", "I", "https://www.senado.gob.mx/informacion/diario/LXV/I"),
    ("LXV", "II", "https://www.senado.gob.mx/informacion/diario/LXV/II"),
    ("LXV", "III", "https://www.senado.gob.mx/informacion/diario/LXV/III"),
]

total = 0
all_links = []
for leg, anio, url in pages:
    r = requests.get(url, headers=headers, verify=False, timeout=20)
    soup = BeautifulSoup(r.text, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        if "/informacion/diario/sesion/" in a["href"]:
            links.append((a["href"].strip(), a.get_text(strip=True)))
    print(f"{leg} Año {anio}: {len(links)} sesiones (first: {links[0] if links else None}, last: {links[-1] if links else None})")
    total += len(links)
    all_links.extend(links)

print(f"Total links across LXIV and LXV: {total} (unique hrefs: {len(set(x[0] for x in all_links))})")

