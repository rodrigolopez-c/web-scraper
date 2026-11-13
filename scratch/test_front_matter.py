import pandas as pd
import re

df = pd.read_csv('informes_rector_iteso.csv', encoding='utf-8-sig')

def strip_front_matter(text: str) -> str:
    if not text:
        return ""

    # Remover líneas de colofón y datos de imprenta / tiraje / edición al inicio
    colophon_patterns = [
        r'Tiraje:\s*[\d,]+\s*ejemplares.*?(?=\n\n|\n[A-ZÁÉÍÓÚÑ])',
        r'Diseño y formación:.*?(?=\n\n|\n[A-ZÁÉÍÓÚÑ])',
        r'Impresión:.*?(?=\n\n|\n[A-ZÁÉÍÓÚÑ])',
        r'D\.R\.\s*©\s*\d{4}.*?(?=\n\n|\n[A-ZÁÉÍÓÚÑ])',
        r'Campus universitario,\s*Periférico Sur.*?(?=\n\n|\n[A-ZÁÉÍÓÚÑ])',
        r'BITNET:.*?INTERNET:.*?(?=\n\n|\n[A-ZÁÉÍÓÚÑ])'
    ]
    for pattern in colophon_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)

    lines = text.split('\n')
    content_start_idx = 0
    
    for idx, line in enumerate(lines[:30]):
        clean_l = line.strip().upper()
        if any(clean_l.startswith(hdr) for hdr in ['INTRODUCCI', 'COMPROMIS', 'MENSAJE', 'INFORME GENERAL', 'CAPÍTULO', 'CAPITULO', '1. ', '1 ']):
            content_start_idx = idx
            break
            
    if content_start_idx > 0 and content_start_idx < len(lines):
        lines = lines[content_start_idx:]
        
    return '\n'.join(lines).strip()

print("=== MUESTRA ITEM 1 LIMPIEZA DE COLOFÓN/PORTADA ===")
raw1 = df['text_clean'].iloc[0]
cleaned1 = strip_front_matter(raw1)
print(cleaned1[:500])

print("\n=== MUESTRA ITEM 15 LIMPIEZA DE COLOFÓN/PORTADA ===")
raw15 = df['text_clean'].iloc[14]
cleaned15 = strip_front_matter(raw15)
print(cleaned15[:500])
