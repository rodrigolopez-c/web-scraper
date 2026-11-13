import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

urls = [
    "https://www.senado.gob.mx/informacion/diario/home",
    "https://www.senado.gob.mx/informacion/diario/LXIV/I",
    "https://www.senado.gob.mx/informacion/diario/LXIV/II",
    "https://www.senado.gob.mx/informacion/diario/LXIV/III",
    "https://www.senado.gob.mx/informacion/diario/LXV",
    "https://www.senado.gob.mx/informacion/diario/LXV/I",
    "https://www.senado.gob.mx/informacion/diario/LXV/II",
    "https://www.senado.gob.mx/informacion/diario/LXV/III",
    "https://www.senado.gob.mx/informacion/diario/LXVI",
    "https://www.senado.gob.mx/informacion/diario/sesion/3011"
]

for u in urls:
    try:
        r = requests.get(u, headers=headers, verify=False, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")
        sesiones = [a["href"] for a in soup.find_all("a", href=True) if "/sesion/" in a["href"] or ".pdf" in a["href"].lower()]
        print(f"URL: {u} | Status: {r.status_code} | Len: {len(r.text)} | Sesiones/PDFs count: {len(sesiones)}")
        if u.endswith("3011") or u.endswith("home") or u.endswith("LXV"):
            fname = "scratch/senado_" + u.split("/")[-1] + ".html"
            with open(fname, "w", encoding="utf-8") as f:
                f.write(r.text)
    except Exception as e:
        print(f"URL: {u} | Error: {e}")

