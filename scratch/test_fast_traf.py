import time
import re
from bs4 import BeautifulSoup
import trafilatura

with open("scratch/senado_3015.html", "r", encoding="utf-8") as f:
    html_str = f.read()

t0 = time.time()
for _ in range(10):
    soup = BeautifulSoup(html_str, "lxml")
    gaceta = soup.find("div", id="gaceta")
    panel_body = gaceta.find("div", class_="panel-body")
    body_rows = panel_body.find_all("div", class_="row", recursive=False)
    row4 = body_rows[4]
    for tbl in row4.find_all("table", class_="forma_tabla"):
        if "Directorio" in tbl.get_text():
            tbl.decompose()
    raw_text = "\n\n".join(body_rows[i].get_text("\n", strip=True) for i in range(1, len(body_rows)))
    # Convert raw_text paragraphs to simple HTML or pass raw_text to trafilatura
    paragraphs_html = "<html><body><article><p>" + "</p><p>".join(
        line for line in raw_text.splitlines() if line.strip()
    ) + "</p></article></body></html>"
    ext = trafilatura.extract(paragraphs_html, fast=True, deduplicate=False)
dt = time.time() - t0
print(f"10x in {dt:.2f}s ({dt/10:.3f}s per doc), len={len(ext) if ext else 0}")
print("First 300 chars:\n", ext[:300] if ext else "")
print("Last 300 chars:\n", ext[-300:] if ext else "")

