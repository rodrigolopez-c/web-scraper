from bs4 import BeautifulSoup

with open("scratch/senado_66_LXIV.html", "r", encoding="utf-8") as f:
    soup_idx = BeautifulSoup(f.read(), "lxml")

links = []
for a in soup_idx.find_all("a", href=True):
    if "/66/diario_de_los_debates/documento/" in a["href"]:
        # check parent context for year/period
        links.append((a["href"], a.get_text(" ", strip=True)))
print(f"LXIV unique doc links: {len(set(x[0] for x in links))}")
print("First 5 links:", links[:5])
print("Last 5 links:", links[-5:])

with open("scratch/senado_66_doc_3762.html", "r", encoding="utf-8") as f:
    soup_doc = BeautifulSoup(f.read(), "lxml")

print("\n--- Doc 3762 structure ---")
for tag in soup_doc.find_all(["h1", "h2", "h3", "h4", "table"])[:15]:
    txt = tag.get_text(" | ", strip=True)
    print(f"Tag <{tag.name}> class={tag.get('class')} (len={len(txt)}): {txt[:200]}")

