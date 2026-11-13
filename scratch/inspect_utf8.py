import pandas as pd

df = pd.read_csv('informes_rector_universal.csv', encoding='utf-8-sig')

sample = df['text_clean'].iloc[0][:500]

print("=== SAMPLE UTF-8 CLEANED TEXT (Item 1) ===")
print(sample)

sample_15 = df['text_clean'].iloc[14][:500]
print("\n=== SAMPLE UTF-8 CLEANED TEXT (Item 15) ===")
print(sample_15)

print("\n¿Contiene \\ufffd (carácter de reemplazo)?", '\ufffd' in ' '.join(df['text_clean'].dropna()))
print("¿Contiene \\xad (soft hyphen)?", '\xad' in ' '.join(df['text_clean'].dropna()))
print("¿Contiene \\xa0 (non-breaking space)?", '\xa0' in ' '.join(df['text_clean'].dropna()))
