from bs4 import BeautifulSoup

with open("scratch/senado_3100.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")
row4 = soup.find("div", id="gaceta").find("div", class_="panel-body").find_all("div", class_="row", recursive=False)[4]
outer_tbl = row4.find("table")
print("Tables inside outer_tbl:", len(outer_tbl.find_all("table")))
for i, t in enumerate(outer_tbl.find_all("table")):
    print(f"  Inner table {i}: len={len(t.get_text())}, attrs={t.attrs}")

