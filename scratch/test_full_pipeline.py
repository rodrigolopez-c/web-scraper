import requests
import re
import unicodedata

def decode_smart_latin1_first(content_bytes: bytes) -> str:
    if not content_bytes:
        return ""
    try:
        text = content_bytes.decode('latin-1')
        if '\ufffd' not in text:
            return text
    except Exception:
        pass
    try:
        return content_bytes.decode('utf-8')
    except Exception:
        return content_bytes.decode('utf-8', errors='replace')

def clean_text_content_advanced(raw_text: str) -> str:
    if not raw_text:
        return ""

    # 0. Normalización Unicode NFC (recombina caracteres diacríticos)
    text = unicodedata.normalize('NFC', raw_text)

    # 1. Eliminar caracteres de formato invisible, guion blando (\xad), espacios no separables (\xa0) y marcas BOM
    text = text.replace('\xad', '').replace('\xa0', ' ').replace('\ufeff', '').replace('\u200b', '')
    
    # Reemplazar ligaturas tipográficas de PDF
    ligatures = {'ﬁ': 'fi', 'ﬂ': 'fl', 'æ': 'ae', 'œ': 'oe'}
    for orig, repl in ligatures.items():
        text = text.replace(orig, repl)

    # 2. Remover caracteres de control ASCII no imprimibles (excepto \n)
    text = re.sub(r'[\r\t\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\ufffd]', '', text)

    # 3. Deshacer palabras divididas por guion al final de línea ('institu-\ncional' -> 'institucional')
    text = re.sub(r'([a-zA-ZáéíóúñÁÉÍÓÚÑ]{2,})-\s*\n\s*([a-zA-ZáéíóúñÁÉÍÓÚÑ]{2,})', r'\1\2', text)

    # 4. Corregir palabras o frases repetidas consecutivamente por artefactos de extracción de PDF
    text = re.sub(r'([A-ZÁÉÍÓÚÑa-záéíóúñ]{4,})\1{2,}', r'\1', text)
    text = re.sub(r'\b([A-ZÁÉÍÓÚÑa-záéíóúñ]{3,})\b(?:\s+\1){2,}', r'\1', text, flags=re.IGNORECASE)

    # 5. Filtrar líneas vacías, números de página aislados y símbolos residuales
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        l = line.strip()
        l = re.sub(r'[ \t]+', ' ', l)
        
        # Remover números de página aislados en líneas solas (ej. '1', '42')
        if re.match(r'^\d{1,4}$', l):
            continue
        
        # Remover símbolos o puntuación solitaria
        if len(l) == 1 and not l.isalnum():
            continue
            
        cleaned_lines.append(l)

    # 6. Reconstruir el flujo continuo de párrafos (unir oraciones partidas entre líneas)
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

r = requests.get('https://rei.iteso.mx/server/api/discover/search/objects?scope=f370375a-1e34-408f-9c2e-2df4b4ee724b&size=5').json()
objects = r['_embedded']['searchResult']['_embedded']['objects']

for idx, obj in enumerate(objects):
    item_id = obj['_embedded']['indexableObject']['id']
    b_res = requests.get(f'https://rei.iteso.mx/server/api/core/items/{item_id}/bundles').json()
    for bundle in b_res.get('_embedded', {}).get('bundles', []):
        if bundle.get('name') == 'TEXT':
            bs_href = bundle['_links']['bitstreams']['href']
            bs = requests.get(bs_href).json()['_embedded']['bitstreams'][0]
            raw = requests.get(bs['_links']['content']['href']).content
            
            raw_text = decode_smart_latin1_first(raw)
            cleaned = clean_text_content_advanced(raw_text)
            
            print(f"\n=== ITEM {idx+1} CLEANED PROSE ===")
            print("Contiene \\ufffd:", '\ufffd' in cleaned)
            print("Contiene 'Ã':", 'Ã' in cleaned)
            print(cleaned[:450])
