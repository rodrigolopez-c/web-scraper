import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
for sid in [3011, 3015, 3016, 3017, 3018]:
    r = requests.get(f"https://www.senado.gob.mx/informacion/diario/sesion/{sid}", headers=headers, verify=False, timeout=15)
    print(f"sid={sid}: status={r.status_code}, len={len(r.text)}, snippet={r.text[:200]!r}")

