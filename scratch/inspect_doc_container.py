from bs4 import BeautifulSoup

with open("scratch/senado_66_doc_3762.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "lxml")

h2 = soup.find("h2", string=lambda s: s and "SENADORES" in s)
if not h2:
    for tag in soup.find_all("h2"):
        if "SENADORES" in tag.get_text() or "PERMANENTE" in tag.get_text():
            h2 = tag
            break

parent = h2.parent if h2 else None
while parent and len(parent.get_text()) < 200000:
    print(f"Parent <{parent.name}> class={parent.get('class')} id={parent.get('id')} text_len={len(parent.get_text())}")
    parent = parent.parent
if parent:
    print(f"Main container <{parent.name}> class={parent.get('class')} id={parent.get('id')} text_len={len(parent.get_text())}")
    for i, child in enumerate(parent.find_all(recursive=False)):
        txt = child.get_text(" | ", strip=True)
        print(f"  Child {i} <{child.name}> class={child.get('class')} id={child.get('id')} len={len(txt)}: {txt[:180]}")

