import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
r = requests.get("https://www.senado.gob.mx/informacion/app/diario/functions/calendarioMes.php?action=ajax&anio=2026&mes=10", headers=headers, verify=False, timeout=15)
print("Status:", r.status_code, "Len:", len(r.text))
print(r.text[:1500])

