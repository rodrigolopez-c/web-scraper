import pandas as pd
import re

def fix_mojibake(text: str) -> str:
    if not text:
        return ""
    
    # 1. Si el texto tiene secuencias UTF-8 mal decodificadas como Latin-1 (Ã¡, Ã³, Ã±, Â©, etc.)
    # Intentar revertir la decodificación errónea Latin-1 -> bytes -> decode UTF-8
    try:
        if 'Ã' in text or 'Â' in text:
            text = text.encode('latin-1').decode('utf-8')
    except Exception:
        pass

    # 2. Reemplazos explícitos de mojibake común si queda algo
    replacements = {
        'Ã¡': 'á', 'Ã©': 'é', 'Ã­': 'í', 'Ã³': 'ó', 'Ãº': 'ú', 'Ã±': 'ñ',
        'Ã\x81': 'Á', 'Ã\x89': 'É', 'Ã\x8d': 'Í', 'Ã\x93': 'Ó', 'Ã\x9a': 'Ú', 'Ã\x91': 'Ñ',
        'Â©': '©', 'Â®': '®', 'Ã¼': 'ü', 'Ã\x9c': 'Ü', 'Âª': 'ª', 'Âº': 'º',
        'Ã\x8dNDICE': 'ÍNDICE', 'Ãndice': 'Índice', 'Ã\x81ndice': 'Índice',
        'Ã': 'á', 'Â': ''
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
        
    return text

def strip_front_matter(text: str) -> str:
    """
    Elimina metadatos de imprenta, tiraje, portada, derechos reservados, índice
    y datos de imprenta iniciales para dejar ÚNICAMENTE el texto limpio del informe.
    """
    if not text:
        return ""

    # Remover tirajes, imprenta, dirección y avisos de derechos reservados iniciales
    text = re.sub(r'Tiraje:\s*[\d,]+\s*ejemplares.*?(?=INTRODUCCI|COMPROMIS|MENSAJE|INFORME|CAP|1\.)', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'D\.R\.\s*©\s*\d{4}.*?(?=INTRODUCCI|COMPROMIS|MENSAJE|INFORME|CAP|1\.)', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'Campus universitario, Periférico Sur.*?(?=INTRODUCCI|COMPROMIS|MENSAJE|INFORME|CAP|1\.)', '', text, flags=re.IGNORECASE | re.DOTALL)

    # Remover portadas y títulos repetidos en el inicio
    text = re.sub(r'^(?:Informe del Rector \d{4}(?:-\d{4})?\s*)+', '', text, flags=re.IGNORECASE).strip()

    return text.strip()

df = pd.read_csv('informes_rector_iteso.csv', encoding='utf-8-sig')
for i in range(5):
    raw = df['text-original'].iloc[i]
    fixed = fix_mojibake(raw)
    clean = strip_front_matter(fixed)
    print(f"\n--- ITEM {i+1} FIXED SAMPLE ---")
    print("Contiene 'Ã':", 'Ã' in clean)
    print("Contiene 'Â':", 'Â' in clean)
    print(clean[:400])
