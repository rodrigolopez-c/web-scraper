import os, sys, pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
curr_dir = os.getcwd()
print("Current Working Directory:", curr_dir)

from build_all_datasets import fetch_all_sessions, process_item_full, ThreadPoolExecutor

items = fetch_all_sessions()
print(f"Cataloged {len(items)} sessions.")

list_universal = []
list_trafilatura = []
list_newspaper = []
list_playwright = []

with ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(process_item_full, items))

for res in results:
    if res:
        u, t, n, p = res
        list_universal.append(u)
        list_trafilatura.append(t)
        list_newspaper.append(n)
        list_playwright.append(p)

columns = ['id', 'language', 'speaker', 'role', 'date', 'context', 'text-original', 'text_clean']

def write_out(data, prefix):
    df = pd.DataFrame(data)[columns]
    xp = os.path.join(curr_dir, f"{prefix}.xlsx")
    cp = os.path.join(curr_dir, f"{prefix}.csv")
    df.to_excel(xp, index=False)
    df.to_csv(cp, index=False, encoding='utf-8-sig')
    print(f"Wrote {xp} ({len(df)} rows)")
    print(f"Wrote {cp} ({len(df)} rows)")

write_out(list_universal, "diario_debates")
write_out(list_trafilatura, "diario_debates_trafilatura")
write_out(list_newspaper, "diario_debates_newspaper")
write_out(list_playwright, "diario_debates_playwright")

print("FINISHED GENERATING FINAL DATASETS!")
