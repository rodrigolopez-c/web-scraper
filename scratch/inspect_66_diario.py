import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

for u in [
    "https://www.senado.gob.mx/66/diario_de_los_debates/LIV/",
    "https://www.senado.gob.mx/66/diario_de_los_debates/LXIV/",
    "https://www.senado.gob.mx/66/diario_de_los_debates/LXV/",
    "https://www.senado.gob.mx/66/diario_de_los_debates/LXVI/",
    "https://www.senado.gob.mx/66/diario_de_los_debates/",
]:
    r = requests.get(u, headers=headers, verify=False, timeout=20)
    soup = BeautifulSoup(r.text, "html.parser")
    links = [(a.get_text(" ", strip=True), a["href"]) for a in soup.find_all("a", href=True) if "diario" in a["href"] or "documento" in a["href"] or "sesion" in a["href"] or ".pdf" in a["href"].lower()]
    print(f"URL: {u} | Status: {r.status_code} | Len: {len(r.text)} | Links: {len(links)}")
    for l in links[:15]:
        print("  ", l)
    if "LXVI" in u or u.endswith("LIV/"):
        with open("scratch/senado_66_" + u.strip("/").split("/")[-1] + ".html", "w", encoding="utf-8") as f:
            f.write(r.text)

