import time
import requests
from concurrent.futures import ThreadPoolExecutor
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def fetch_one(sid):
    url = f"https://www.senado.gob.mx/informacion/diario/sesion/{sid}"
    for attempt in range(4):
        try:
            r = requests.get(url, headers=headers, verify=False, timeout=25)
            if r.status_code == 200 and "DIARIO DE LOS DEBATES" in r.text:
                return sid, len(r.text), attempt
            time.sleep(1.0 * (attempt + 1))
        except Exception as e:
            time.sleep(1.0 * (attempt + 1))
    return sid, 0, -1

sids = [3011, 3015, 3016, 3017, 3018, 3019, 3020, 3021, 3022, 3023, 3024, 3025, 3026, 3027, 3028, 3030, 3031, 3032, 3033, 3034]
t0 = time.time()
with ThreadPoolExecutor(max_workers=6) as ex:
    res = list(ex.map(fetch_one, sids))
dt = time.time() - t0
ok = sum(1 for _, l, _ in res if l > 13000)
print(f"Fetched {ok}/{len(sids)} in {dt:.2f}s:")
for item in res:
    print(" ", item)

