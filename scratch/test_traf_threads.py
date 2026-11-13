from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
import trafilatura

with open("scratch/senado_3015.html", "r", encoding="utf-8") as f:
    html_str = f.read()

def work(i):
    soup = BeautifulSoup(html_str, "html.parser")
    row4 = soup.find("div", id="gaceta").find("div", class_="panel-body").find_all("div", class_="row", recursive=False)[4]
    outer_tbl = row4.find("table")
    if outer_tbl:
        for tag in outer_tbl.find_all(["tbody", "tr", "td"], recursive=False):
            for sub in tag.find_all(["tr", "td"], recursive=False):
                sub.unwrap()
            tag.unwrap()
        outer_tbl.unwrap()
    debate_html = "<html><body><article>\n" + str(row4) + "\n</article></body></html>"
    ext = trafilatura.extract(debate_html, include_tables=True, deduplicate=False)
    return len(ext) if ext else 0

with ThreadPoolExecutor(max_workers=8) as ex:
    res = list(ex.map(work, range(24)))
print("Results:", set(res), "Count:", len(res))

