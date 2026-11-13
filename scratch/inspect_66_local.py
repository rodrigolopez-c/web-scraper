from bs4 import BeautifulSoup

with open("scratch/senado_66_LXVI.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

doc_links = []
for a in soup.find_all("a", href=True):
    if "/documento/" in a["href"] or "/diario_de_los_debates/" in a["href"]:
        doc_links.append((a.get_text(" ", strip=True), a["href"]))

print(f"Total doc/diario links: {len(doc_links)}")
for l in doc_links[:40]:
    print(" ", l)
print("...")
for l in doc_links[-20:]:
    print(" ", l)

