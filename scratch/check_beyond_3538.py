import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
for sid in [3538, 3539, 3540, 3545]:
    r = requests.get(f"https://www.senado.gob.mx/informacion/diario/sesion/{sid}", headers=headers, verify=False, timeout=15)
    has_debate = "Versi&oacute;n para descarga" in r.text or "PRESIDENCIA" in r.text or "PRESIDE" in r.text
    print(f"sid={sid}: len={len(r.text)}, has_debate={has_debate}")

