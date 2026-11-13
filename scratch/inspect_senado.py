import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://www.senado.gob.mx/informacion/diario/LXIV"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

r = requests.get(url, headers=headers, verify=False, timeout=20)
print("Status:", r.status_code)
print("Length:", len(r.text))
with open("scratch/senado_lxiv.html", "w", encoding="utf-8") as f:
    f.write(r.text)

soup = BeautifulSoup(r.text, "html.parser")
for a in soup.find_all("a", href=True)[:40]:
    print(a.get_text(strip=True), "->", a["href"])

