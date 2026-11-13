from bs4 import BeautifulSoup
import trafilatura

for sid in ["3011", "3015", "3100", "3278", "3400"]:
    with open(f"scratch/senado_{sid}.html", "r", encoding="utf-8") as f:
        html_str = f.read()
    soup = BeautifulSoup(html_str, "html.parser")
    
    # Inspect header metadata
    gaceta = soup.find("div", id="gaceta")
    rows = gaceta.find_all("div", class_="row", recursive=False) if gaceta else []
    panel_body = gaceta.find("div", class_="panel-body") if gaceta else None
    body_rows = panel_body.find_all("div", class_="row", recursive=False) if panel_body else []
    print(f"=== Session {sid} (body_rows={len(body_rows)}) ===")
    for idx, r in enumerate(body_rows):
        txt = r.get_text(" | ", strip=True)
        print(f"  Row {idx} (len={len(txt)}): {txt[:220]}")

