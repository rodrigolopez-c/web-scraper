import re
from bs4 import BeautifulSoup

for leg in ["LXIV", "LXV", "LXVI"]:
    with open(f"scratch/senado_66_{leg}.html", "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "lxml")
    sids = []
    for a in soup.find_all("a", href=True):
        m = re.search(r'/66/diario_de_los_debates/documento/(\d+)', a["href"])
        if m:
            txt = a.get_text(" ", strip=True)
            # Exclude the top banner link to the latest session of LXVI (3762) when parsing LXIV/LXV
            if "Legislatura" in txt or "Año de ejercicio" in txt:
                continue
            sids.append((int(m.group(1)), txt))
    unique_sids = sorted(set(x[0] for x in sids))
    print(f"Leg {leg}: count={len(unique_sids)}, min={min(unique_sids)}, max={max(unique_sids)}")

