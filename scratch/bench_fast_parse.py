import time
import re
from bs4 import BeautifulSoup
import trafilatura

with open("scratch/senado_3015.html", "r", encoding="utf-8") as f:
    html_str = f.read()

t0 = time.time()
for _ in range(10):
    # Extract the gaceta panel-body slice directly or with lxml
    soup = BeautifulSoup(html_str, "lxml")
    gaceta = soup.find("div", id="gaceta")
    panel_body = gaceta.find("div", class_="panel-body")
    body_rows = panel_body.find_all("div", class_="row", recursive=False)
    row4 = body_rows[4]
    for tbl in row4.find_all("table", class_="forma_tabla"):
        if "Directorio" in tbl.get_text() and len(tbl.get_text()) < 1000:
            tbl.decompose()
    text_original = "\n\n".join(body_rows[i].get_text("\n", strip=True) for i in range(1, len(body_rows)))
    # Fast paragraph HTML for trafilatura fast=True
    lines = [line.strip() for line in row4.get_text("\n").splitlines() if line.strip()]
    fast_html = "<html><body><article><p>" + "</p>\n<p>".join(lines) + "</p></article></body></html>"
    traf_extracted = trafilatura.extract(fast_html, fast=True, deduplicate=False)
dt = time.time() - t0
print(f"10 docs in {dt:.2f}s ({dt/10:.3f}s/doc), orig_len={len(text_original)}, traf_len={len(traf_extracted)}")

