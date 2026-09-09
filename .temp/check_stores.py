import requests
import json
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/html, */*'
}

print("=== 1. TESTE KABUM ===")
try:
    url = 'https://servicespub.prod.api.aws.grupokabum.com.br/catalog/v2/products?query=RTX%205070'
    r = requests.get(url, headers=headers, timeout=10)
    if r.status_code == 200:
        data = r.json()
        items = data.get('data', [])
        print(f"KaBuM retornou {len(items)} itens.")
        for it in items[:12]:
            attr = it.get('attributes', {})
            name = attr.get('title', '')
            price = attr.get('price', 0)
            pid = it.get('id', '')
            fname = attr.get('friendly_name', '')
            link = f"https://www.kabum.com.br/produto/{pid}/{fname}"
            print(f"- [{pid}] {name[:60]} | Preço: {price} | Link: {link}")
    else:
        print("KaBuM Status:", r.status_code)
except Exception as e:
    print("KaBuM Erro:", e)

print("\n=== 2. TESTE PICHAU ===")
try:
    url = "https://www.pichau.com.br/search?q=RTX%205070"
    r = requests.get(url, headers=headers, timeout=10)
    print("Pichau Status:", r.status_code)
    if r.status_code == 200:
        match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', r.text)
        if match:
            pj = json.loads(match.group(1))
            props = pj.get('props', {}).get('pageProps', {})
            print("Pichau keys:", list(props.keys()))
            st = props.get('initialState', {}) or props.get('apolloState', {})
            count = 0
            for k, v in st.items():
                if isinstance(v, dict) and ('name' in v or 'title' in v):
                    t = v.get('name') or v.get('title')
                    ukey = v.get('url_key') or ''
                    price = v.get('price') or v.get('final_price') or v.get('regular_price')
                    print(f"- Pichau item: {t[:60]} | url_key: {ukey} | Preço: {price}")
                    count += 1
                    if count >= 8:
                        break
except Exception as e:
    print("Pichau Erro:", e)

print("\n=== 3. TESTE TERABYTE ===")
try:
    url = "https://www.terabyteshop.com.br/busca?str=RTX+5070"
    r = requests.get(url, headers=headers, timeout=10)
    print("Terabyte Status:", r.status_code)
    if r.status_code == 200:
        prod_blocks = re.findall(r'<div class="pbox[^"]*"[^>]*>(.*?)</div>\s*</div>\s*</div>', r.text, re.DOTALL)
        print(f"Terabyte encontrou {len(prod_blocks)} blocos de produto.")
        for b in prod_blocks[:8]:
            title_m = re.search(r'<a class="prod-name"[^>]*title="([^"]+)"', b) or re.search(r'<a class="prod-name"[^>]*>([^<]+)</a>', b)
            url_m = re.search(r'<a href="([^"]+)" class="prod-name"', b)
            if title_m:
                t = title_m.group(1).strip()
                u = url_m.group(1) if url_m else ""
                print(f"- Terabyte item: {t[:60]} | Link: {u}")
except Exception as e:
    print("Terabyte Erro:", e)
