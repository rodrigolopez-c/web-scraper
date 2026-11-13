import pandas as pd

df = pd.read_csv("datasets/diario_debates_trafilatura.csv", nrows=5)
print("Columns:", df.columns.tolist())
for i, row in df.iterrows():
    print(f"--- Row {i} ---")
    for col in df.columns:
        val = str(row[col])
        if len(val) > 200:
            val = val[:200] + f"... [len={len(val)}]"
        print(f"  {col}: {val}")

