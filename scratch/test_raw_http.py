import requests

url_search = 'https://rei.iteso.mx/server/api/discover/search/objects?scope=f370375a-1e34-408f-9c2e-2df4b4ee724b&size=10'
res = requests.get(url_search).json()
objects = res['_embedded']['searchResult']['_embedded']['objects']

for i in [0, 1, 5, 8]:
    item_id = objects[i]['_embedded']['indexableObject']['id']
    bundles_res = requests.get(f'https://rei.iteso.mx/server/api/core/items/{item_id}/bundles').json()
    for bundle in bundles_res.get('_embedded', {}).get('bundles', []):
        if bundle.get('name') == 'TEXT':
            bs_url = bundle['_links']['bitstreams']['href']
            bs_res = requests.get(bs_url).json()
            bs = bs_res['_embedded']['bitstreams'][0]
            content_url = bs['_links']['content']['href']
            
            raw_bytes = requests.get(content_url).content
            print(f"\n--- ITEM {i+1} RAW BYTES ---")
            print("Contains b'\\xef\\xbf\\xbd' (UTF-8 replacement char):", b'\xef\xbf\xbd' in raw_bytes)
            print("Contains b'\\xe1' (Latin-1 á):", b'\xe1' in raw_bytes)
            print("Contains b'\\xe9' (Latin-1 é):", b'\xe9' in raw_bytes)
            print("Contains b'\\xf3' (Latin-1 ó):", b'\xf3' in raw_bytes)
            print("Contains b'\\xf1' (Latin-1 ñ):", b'\xf1' in raw_bytes)
            
            # Decodificar con latin-1 vs utf-8
            t_latin1 = raw_bytes.decode('latin-1', errors='replace')
            t_utf8 = raw_bytes.decode('utf-8', errors='replace')
            print("Latin-1 sample:", repr(t_latin1[100:250]))
            print("UTF-8 sample:  ", repr(t_utf8[100:250]))
