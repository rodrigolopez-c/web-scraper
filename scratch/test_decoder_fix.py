import requests
import re

def decode_smart_fixed(content_bytes: bytes) -> str:
    if not content_bytes:
        return ""
    
    # 1. Intentar UTF-8 estricto (SIN errors='replace')
    try:
        text = content_bytes.decode('utf-8')
        # Verificar que no contenga \ufffd (el carácter de reemplazo)
        if '\ufffd' not in text and b'\xef\xbf\xbd' not in content_bytes:
            return text
    except UnicodeDecodeError:
        pass

    # 2. Si falló UTF-8 estricto o tenía b'\xef\xbf\xbd', probar Latin-1 / CP1252 / ISO-8859-1
    for enc in ['latin-1', 'cp1252', 'iso-8859-1']:
        try:
            return content_bytes.decode(enc)
        except Exception:
            pass

    return content_bytes.decode('utf-8', errors='replace')

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
            txt = decode_smart_fixed(raw)
            print(f"\n=== ITEM {idx+1} FIXED DECODE ===")
            print("Contiene \\ufffd:", '\ufffd' in txt)
            print("Muestra:", repr(txt[100:300]))
