import requests
import json
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

print("=== PICHAU NEXT DATA ===")
r = requests.get('https://www.pichau.com.br/hardware/placa-de-video', headers=headers)
match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', r.text)
if match:
    data = json.loads(match.group(1))
    st = data.get('props', {}).get('pageProps', {}).get('initialState', {})
    print("Total chaves no initialState Pichau:", len(st))
    for k, v in list(st.items())[:30]:
        if isinstance(v, dict) and ('name' in v or 'title' in v or 'url_key' in v):
            name = v.get('name') or v.get('title')
            ukey = v.get('url_key')
            price = v.get('price')
            print(f"- {name} | url_key: {ukey} | Preço: {price}")
else:
    print("Nenhum NEXT_DATA encontrado na Pichau.")
