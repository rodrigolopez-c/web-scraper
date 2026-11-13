import os, sys, pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
target_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print("Target dir resolved to:", target_dir)

from build_all_datasets import fetch_all_sessions, process_item_full, ThreadPoolExecutor

items = fetch_all_sessions()
print(f"Total cataloged items: {len(items)}")

list_universal = []
list_trafilatura = []
list_newspaper = []
list_playwright = []

with ThreadPoolExecutor(max_workers=16) as executor:
    results = list(executor.map(process_item_full, items))

for res in results:
    if res:
        u, t, n, p = res
        list_universal.append(u)
        list_trafilatura.append(t)
        list_newspaper.append(n)
        list_playwright.append(p)

columns = ['id', 'language', 'speaker', 'role', 'date', 'context', 'text-original', 'text_clean']

datasets = {
    "diario_debates": list_universal,
    "diario_debates_trafilatura": list_trafilatura,
    "diario_debates_newspaper": list_newspaper,
    "diario_debates_playwright": list_playwright
}

for name, data in datasets.items():
    df = pd.DataFrame(data)[columns]
    xlsx_p = os.path.join(target_dir, f"{name}.xlsx")
    csv_p = os.path.join(target_dir, f"{name}.csv")
    df.to_excel(xlsx_p, index=False)
    df.to_csv(csv_p, index=False, encoding='utf-8-sig')
    print(f"SAVED: {xlsx_p} ({len(df)} rows)")
    print(f"SAVED: {csv_p} ({len(df)} rows)")

print("ALL FILES WRITTEN SUCCESSFULLY TO TARGET DIR!")
