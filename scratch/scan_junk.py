import pandas as pd
import re

df = pd.read_csv('informes_rector_universal.csv')
all_text = ' '.join(df['text_clean'].dropna().tolist())

# Categorizar caracteres
valid_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789áéíóúñÁÉÍÓÚÑüÜ \n\t.,;:?!-()\"'$%&/=@+#%*<>[]{}°|_®©«»¡¿—–’‘“”•…")

junk_found = {}
for char in all_text:
    if char not in valid_chars:
        code = f"U+{ord(char):04X}"
        junk_found[code] = (char, junk_found.get(code, (char, 0))[1] + 1)

print("=== CARACTERES RULOS/BASURA DETECTADOS ===")
for code, (char, count) in sorted(junk_found.items()):
    print(f"Code: {code} | Char: {repr(char)} | Count: {count}")
