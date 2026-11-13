import trafilatura
from bs4 import BeautifulSoup

with open("scratch/senado_3011.html", "r", encoding="utf-8") as f:
    html_content = f.read()

extracted = trafilatura.extract(html_content, include_tables=True, deduplicate=False)
print("Trafilatura full HTML len:", len(extracted) if extracted else 0)
if extracted:
    print("Preview first 500 chars:\n", extracted[:500])
    print("\nPreview last 500 chars:\n", extracted[-500:])

soup = BeautifulSoup(html_content, "html.parser")
gaceta = soup.find("div", id="gaceta")
if gaceta:
    raw_text = gaceta.get_text("\n", strip=True)
    print("\nRaw gaceta text len:", len(raw_text))

