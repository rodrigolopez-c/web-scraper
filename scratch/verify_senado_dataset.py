import os
import pandas as pd

csv_path = "datasets/diario_debates_senado_trafilatura.csv"
xlsx_path = "datasets/diario_debates_senado_trafilatura.xlsx"

print("CSV size (MB):", os.path.getsize(csv_path) / (1024 * 1024))
print("XLSX size (MB):", os.path.getsize(xlsx_path) / (1024 * 1024))

df = pd.read_csv(csv_path)
print("Total rows:", len(df))
print("Columns:", df.columns.tolist())
print("Null counts:\n", df.isnull().sum())
print("\nBreakdown by Legislature prefix:")
print(df['id'].apply(lambda x: x.split('-')[1]).value_counts())
print("\nDate range:", df['date'].min(), "to", df['date'].max())
print("\nTop 10 speakers:\n", df['speaker'].value_counts().head(10))
print("\nSample rows (first of each legislature):")
for leg in ["LXIV", "LXV", "LXVI"]:
    sub = df[df['id'].str.contains(f"DD-{leg}-")].iloc[0]
    print(f"  {sub['id']} | {sub['date']} | {sub['speaker']} | {sub['role']} | {sub['context'][:80]}... | clean_len={len(str(sub['text_clean']))}")

