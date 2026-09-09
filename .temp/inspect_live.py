import requests
import re
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'pt-BR,pt;q=0.9',
}

print("=== TERABYTE CHECK ===")
url_tb = "https://www.terabyteshop.com.br/busca?str=RTX+5070+Ti"
r = requests.get(url_tb, headers=headers, timeout=10)
print(f"Status: {r.status_code}")
prod_blocks = re.findall(r'<div class="pbox[^"]*"[^>]*>(.*?)</div>\s*</div>\s*</div>', r.text, re.DOTALL)
print(f"Blocos encontrados: {len(prod_blocks)}")
for b in prod_blocks:
    title_m = re.search(r'<a class="prod-name"[^>]*title="([^"]+)"', b)
    if not title_m:
        title_m = re.search(r'<a class="prod-name"[^>]*>([^<]+)</a>', b)
    url_m = re.search(r'<a href="([^"]+)" class="prod-name"', b)
    price_m = re.search(r'class="prod-juros"[^>]*>.*?R\$\s*([\d\.,]+)', b, re.DOTALL)
    if title_m:
        t = title_m.group(1).strip()
        u = url_m.group(1) if url_m else 'sem url'
        p = price_m.group(1) if price_m else 'sem preco'
        print(f"  [TB] {t} | Preco 12x: {p} | URL: https://www.terabyteshop.com.br{u}")

print("\n=== KABUM CHECK ===")
for q in ["RTX 5070 Ti", "5070 Ti"]:
    url_kb = f"https://servicespub.prod.api.aws.grupokabum.com.br/catalog/v2/products?query={requests.utils.quote(q)}&page=1&limit=20"
    r = requests.get(url_kb, headers=headers, timeout=10)
    data = r.json()
    for item in data.get('data', []):
        name = item.get('attributes', {}).get('title') or item.get('name')
        code = item.get('id') or item.get('code')
        slug = item.get('attributes', {}).get('slug') or item.get('friendlyName') or ''
        price_card = item.get('attributes', {}).get('price')
        avail = item.get('attributes', {}).get('available')
        if '5070' in name.upper() and 'TI' in name.upper():
            print(f"  [KB] ID: {code} | {name} | Preco: R$ {price_card} | URL: https://www.kabum.com.br/produto/{code}/{slug}")
