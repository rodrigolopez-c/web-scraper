import time
from bs4 import BeautifulSoup
import trafilatura

with open("scratch/senado_3015.html", "r", encoding="utf-8") as f:
    html_str = f.read()

t0 = time.time()
for _ in range(5):
    soup = BeautifulSoup(html_str, "html.parser")
print("html.parser 5x:", time.time() - t0)

t0 = time.time()
for _ in range(5):
    soup = BeautifulSoup(html_str, "lxml")
print("lxml 5x:", time.time() - t0)

t0 = time.time()
for _ in range(5):
    ext = trafilatura.extract(html_str, include_tables=False, deduplicate=False, favor_precision=False, no_fallback=True)
print("trafilatura no_fallback 5x:", time.time() - t0, "len:", len(ext) if ext else 0)

