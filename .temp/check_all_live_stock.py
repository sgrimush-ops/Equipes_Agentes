import requests
import json
import re
import sys

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'pt-BR,pt;q=0.9',
}

print("========================================")
print("1. VERIFICANDO KABUM (API DIRETA)")
print("========================================")
url_kb = 'https://servicespub.prod.api.aws.grupokabum.com.br/catalog/v2/products?query=RTX%205070%20Ti&page=1&limit=30'
kabum_valid = []
try:
    r = requests.get(url_kb, headers=headers, timeout=10)
    data = r.json()
    items = data.get('data', [])
    for item in items:
        attrs = item.get('attributes', {})
        name = attrs.get('title') or item.get('name', '')
        code = item.get('id') or item.get('code')
        slug = attrs.get('slug') or item.get('friendlyName') or ''
        price = attrs.get('price') or 0.0
        avail = attrs.get('available', False)
        
        # Check if actually 5070 Ti
        name_u = name.upper()
        if '5070' in name_u and 'TI' in name_u and not 'NOTEBOOK' in name_u:
            link = f"https://www.kabum.com.br/produto/{code}/{slug}" if slug else f"https://www.kabum.com.br/produto/{code}"
            kabum_valid.append({
                'id': code,
                'title': name,
                'price': price,
                'avail': avail,
                'url': link
            })
            print(f"  [KaBuM ATIVA] ID {code} | {name} | R$ {price:.2f} (10x de R$ {price/10:.2f}) | Disp: {avail} | {link}")
except Exception as e:
    print(f"Erro KaBuM: {e}")

print(f"\nTotal KaBuM válidas e reais: {len(kabum_valid)}")

print("\n========================================")
print("2. VERIFICANDO TERABYTESHOP")
print("========================================")
tb_urls = [
    'https://www.terabyteshop.com.br/busca?str=RTX+5070+Ti',
    'https://www.terabyteshop.com.br/hardware/placas-de-video/nvidia-geforce/geforce-rtx-50-series/rtx-5070-ti',
    'https://www.terabyteshop.com.br/produto/43110/placa-de-video-palit-geforce-rtx-5070-ti-gamingpro-oc-16gb',
    'https://www.terabyteshop.com.br/produto/37442/placa-de-video-inno3d-nvidia-geforce-rtx-5070-ti-x3-oc-white-16gb-gddr7-dlss-ray-tracing-n507t3-16d7x-176068w'
]

for u in tb_urls:
    try:
        r = requests.get(u, headers=headers, timeout=8, allow_redirects=True)
        print(f"URL: {u} -> Status: {r.status_code} | URL Final: {r.url}")
        if r.status_code == 200:
            if 'produto-esgotado' in r.text.lower() or 'avise-me' in r.text.lower():
                print("    -> PRODUTO ESGOTADO / INDISPONÍVEL!")
            elif 'class="prod-name"' in r.text:
                print("    -> Contém produtos listados.")
            elif 'ops! nenhum produto' in r.text.lower() or 'não encontramos' in r.text.lower():
                print("    -> NENHUM PRODUTO ENCONTRADO!")
    except Exception as e:
        print(f"URL: {u} -> Erro: {e}")

print("\n========================================")
print("3. VERIFICANDO PICHAU")
print("========================================")
pc_urls = [
    'https://www.pichau.com.br/hardware/placa-de-video?fabricante_gpu=5561',
    'https://www.pichau.com.br/search?q=RTX%205070%20Ti'
]
for u in pc_urls:
    try:
        r = requests.get(u, headers=headers, timeout=8, allow_redirects=True)
        print(f"URL: {u} -> Status: {r.status_code} | URL Final: {r.url}")
    except Exception as e:
        print(f"URL: {u} -> Erro: {e}")
