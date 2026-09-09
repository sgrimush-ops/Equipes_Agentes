import requests
import re
import json

url = 'https://www.terabyteshop.com.br/produto/37704/placa-de-video-palit-nvidia-geforce-rtx-5070-ti-gamingpro-s-16gb-gddr7-dlss-ray-tracing-ne7507t019t2-gb2031u'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'pt-BR,pt;q=0.9',
}

r = requests.get(url, headers=headers, timeout=12)
print("Status HTTP:", r.status_code)
print("URL Final:", r.url)

html = r.text

# Extract Title
title_m = re.search(r'<h1[^>]*class="tit-prod"[^>]*>(.*?)</h1>', html, re.DOTALL)
if not title_m:
    title_m = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
title = re.sub(r'<[^>]+>', '', title_m.group(1)).strip() if title_m else "Não encontrado"
print(f"Título: {title}")

# Extract Prices
# Em 12x no cartão
juros_m = re.search(r'id="valParc"[^>]*>.*?R\$\s*([\d\.,]+)', html, re.DOTALL)
if not juros_m:
    juros_m = re.search(r'class="valParc"[^>]*>.*?R\$\s*([\d\.,]+)', html, re.DOTALL)
if not juros_m:
    juros_m = re.search(r'12x de.*?R\$\s*([\d\.,]+)', html, re.DOTALL | re.IGNORECASE)

print(f"Match Parcela 12x: {juros_m.group(0) if juros_m else 'Não encontrado'}")

# Preço a prazo total
total_card_m = re.search(r'id="valTotalCartao"[^>]*>.*?R\$\s*([\d\.,]+)', html, re.DOTALL)
if not total_card_m:
    total_card_m = re.search(r'class="valTotalCartao"[^>]*>.*?R\$\s*([\d\.,]+)', html, re.DOTALL)
if not total_card_m:
    total_card_m = re.search(r'total a prazo.*?R\$\s*([\d\.,]+)', html, re.DOTALL | re.IGNORECASE)

print(f"Match Total Cartão: {total_card_m.group(0) if total_card_m else 'Não encontrado'}")

# Check any other price spans or json-ld
json_ld_matches = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
for j in json_ld_matches:
    try:
        data = json.loads(j)
        print("JSON-LD:", json.dumps(data, indent=2, ensure_ascii=False))
    except Exception:
        pass

# Check button / stock
if 'indisponivel' in html.lower() or 'avise-me' in html.lower() or 'produto-esgotado' in html.lower():
    print("Estoque: AVISO DE INDISPONÍVEL / AVISE-ME ENCONTRADO NO HTML")
if 'btn-comprar' in html.lower() or 'comprar' in html.lower():
    print("Possui menção a botão Comprar")

# Look for price occurrences in raw text
prices = re.findall(r'R\$\s*[\d\.,]+', html)
print(f"Primeiros 10 preços encontrados no HTML: {prices[:10]}")
