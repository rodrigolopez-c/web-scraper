from bs4 import BeautifulSoup
import trafilatura

with open("scratch/senado_3011.html", "r", encoding="utf-8") as f:
    html_str = f.read()

soup = BeautifulSoup(html_str, "html.parser")
gaceta = soup.find("div", id="gaceta")
panel_body = gaceta.find("div", class_="panel-body")
body_rows = panel_body.find_all("div", class_="row", recursive=False)

row4 = body_rows[4]
for tbl in row4.find_all("table", class_="forma_tabla"):
    tbl.decompose()

# Unwrap the outer layout table in row4 so paragraphs <p> are preserved as paragraphs!
outer_tbl = row4.find("table")
if outer_tbl:
    for tr in outer_tbl.find_all("tr", recursive=False):
        tr.unwrap()
    for td in outer_tbl.find_all("td", recursive=False):
        td.unwrap()
    outer_tbl.unwrap()

debate_html = "<html><body><article>\n" + str(row4) + "\n</article></body></html>"
extracted = trafilatura.extract(debate_html, include_tables=True, deduplicate=False)
print("Extracted len:", len(extracted) if extracted else 0)
print("First 1000 chars:\n", extracted[:1000] if extracted else "")
print("\nLast 500 chars:\n", extracted[-500:] if extracted else "")

