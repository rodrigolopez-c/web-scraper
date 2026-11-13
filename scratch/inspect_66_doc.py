import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

for leg in ["LXIV", "LXV", "LXVI"]:
    r = requests.get(f"https://www.senado.gob.mx/66/diario_de_los_debates/{leg}/", headers=headers, verify=False, timeout=20)
    with open(f"scratch/senado_66_{leg}.html", "w", encoding="utf-8") as f:
        f.write(r.text)
    soup = BeautifulSoup(r.text, "lxml")
    doc_links = [a["href"] for a in soup.find_all("a", href=True) if "/documento/" in a["href"]]
    sub_links = [a["href"] for a in soup.find_all("a", href=True) if f"/diario_de_los_debates/{leg}/" in a["href"]]
    print(f"Leg {leg}: doc_links={len(doc_links)}, sub_links={sub_links}")

r_doc = requests.get("https://www.senado.gob.mx/66/diario_de_los_debates/documento/3762", headers=headers, verify=False, timeout=20)
with open("scratch/senado_66_doc_3762.html", "w", encoding="utf-8") as f:
    f.write(r_doc.text)
print("Doc 3762 len:", len(r_doc.text))

