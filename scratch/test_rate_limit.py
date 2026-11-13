import time
import requests
from concurrent.futures import ThreadPoolExecutor
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def test_batch(n_workers, count):
    sids = list(range(3015, 3015 + count))
    def get_one(sid):
        r = requests.get(f"https://www.senado.gob.mx/informacion/diario/sesion/{sid}", headers=headers, verify=False, timeout=20)
        return sid, r.status_code, len(r.text), ("DIARIO DE LOS DEBATES" in r.text)
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=n_workers) as ex:
        results = list(ex.map(get_one, sids))
    dt = time.time() - t0
    valid = [x for x in results if x[3]]
    invalid = [x for x in results if not x[3]]
    print(f"workers={n_workers}, count={count}, time={dt:.2f}s, valid={len(valid)}, invalid={len(invalid)}")
    if invalid:
        print("  Sample invalid:", invalid[:5])

test_batch(8, 40)

