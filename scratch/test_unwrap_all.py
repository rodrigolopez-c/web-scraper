from bs4 import BeautifulSoup
import trafilatura

for sid in ["3011", "3015", "3100", "3278", "3400"]:
    with open(f"scratch/senado_{sid}.html", "r", encoding="utf-8") as f:
        html_str = f.read()
    soup = BeautifulSoup(html_str, "html.parser")
    gaceta = soup.find("div", id="gaceta")
    panel_body = gaceta.find("div", class_="panel-body")
    body_rows = panel_body.find_all("div", class_="row", recursive=False)
    row4 = body_rows[4]
    
    # Raw text before unwrapping/decomposing
    text_original = "\n".join(body_rows[i].get_text("\n", strip=True) for i in range(1, len(body_rows)))
    
    for tbl in row4.find_all("table", class_="forma_tabla"):
        tbl.decompose()
    outer_tbl = row4.find("table")
    if outer_tbl:
        for tag in outer_tbl.find_all(["tbody", "tr", "td"], recursive=False):
            for sub in tag.find_all(["tr", "td"], recursive=False):
                sub.unwrap()
            tag.unwrap()
        outer_tbl.unwrap()
    debate_html = "<html><body><article>\n" + str(row4) + "\n</article></body></html>"
    extracted = trafilatura.extract(debate_html, include_tables=True, deduplicate=False)
    print(f"sid={sid}: orig_len={len(text_original)}, traf_len={len(extracted) if extracted else 0}")
    print("  First 200:", (extracted[:200] if extracted else "").replace("\n", " / "))

