import pandas as pd
import re
import unicodedata

def clean_and_normalize_text(text: str) -> str:
    if not text:
        return ""
    
    # 0. Reparar codificación doble UTF-8 (ej. '\xc3\xa1' leído como Latin-1 'Ã¡')
    try:
        # Si contiene secuencias típicas de UTF-8 mala decodificación (Ã, Â, etc.)
        if 'Ã' in text or 'Â' in text:
            reencoded = text.encode('raw_unicode_escape').decode('utf-8')
            text = reencoded
    except Exception:
        pass

    # 1. Normalizar Unicode (NFC para combinar diacríticos y letras acentuadas)
    text = unicodedata.normalize('NFC', text)

    # 2. Reemplazar ligaturas tipográficas comunes de PDF
    ligatures = {
        'ﬁ': 'fi', 'ﬂ': 'fl', 'æ': 'ae', 'œ': 'oe',
        'FEFF': '', 'u200b': '', '\xad': '', '\xa0': ' '
    }
    for orig, repl in ligatures.items():
        text = text.replace(orig, repl)

    # 3. Remover caracteres de control y formato invisible
    text = re.sub(r'[\r\t\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\xad\ufeff\u200b-\u200d\u2060]', '', text)

    # 4. Deshacer palabras partidas por guion al final de línea ('institu-\ncional' -> 'institucional')
    text = re.sub(r'([a-zA-ZáéíóúñÁÉÍÓÚÑ]{2,})-\s*\n\s*([a-zA-ZáéíóúñÁÉÍÓÚÑ]{2,})', r'\1\2', text)

    # 5. Corregir palabras/frases repetidas pegadas por OCR
    text = re.sub(r'([A-ZÁÉÍÓÚÑa-záéíóúñ]{4,})\1{2,}', r'\1', text)

    # 6. Procesar por líneas
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        l = line.strip()
        l = re.sub(r'[ \t\xa0]+', ' ', l)
        
        # Eliminar números de página aislados (ej. '1', '42')
        if re.match(r'^\d{1,4}$', l):
            continue
        
        # Eliminar líneas solas de caracteres especiales no alfanuméricos
        if len(l) == 1 and not l.isalnum():
            continue
            
        cleaned_lines.append(l)

    # 7. Unir oraciones interrumpidas por saltos de línea de PDF
    processed_paragraphs = []
    current_para = []
    
    for line in cleaned_lines:
        if not line:
            if current_para:
                processed_paragraphs.append(' '.join(current_para))
                current_para = []
        else:
            if current_para:
                prev = current_para[-1]
                if prev and not prev[-1] in '.!?:;':
                    current_para.append(line)
                else:
                    processed_paragraphs.append(' '.join(current_para))
                    current_para = [line]
            else:
                current_para = [line]
                
    if current_para:
        processed_paragraphs.append(' '.join(current_para))
        
    result = '\n\n'.join(p for p in processed_paragraphs if p.strip())
    result = re.sub(r'[ \t]+', ' ', result)
    return result.strip()

# Probar con un texto
df = pd.read_csv('informes_rector_universal.csv')
sample = df['text-original'].iloc[14]
cleaned = clean_and_normalize_text(sample)

with open('scratch/sample_cleaned.txt', 'w', encoding='utf-8') as f:
    f.write(cleaned[:2000])

print("Limpieza realizada con éxito. Muestra de los primeros 500 caracteres:")
print(cleaned[:500])
