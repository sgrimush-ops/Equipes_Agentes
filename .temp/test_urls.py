import requests

links_to_test = [
    ("KaBuM Palit GamingPro-S", "https://www.kabum.com.br/produto/988703/placa-de-video-palit-geforce-rtx-5070-ti-16gb-gamingpro-s-gddr7-256bits-ne7507t019t2-gb2031u"),
    ("KaBuM ASUS Prime 5070 Ti", "https://www.kabum.com.br/produto/706473/placa-de-video-asus-prime-rtx-5070-ti-o16g-nvidia-geforce-16gb-gddr7-90yv0ly0-m0na00"),
    ("KaBuM ASUS ROG Strix 5070 Ti", "https://www.kabum.com.br/produto/761536/placa-de-video-asus-rog-strix-rtx-5070-ti-oc-16g-gaming-nvidia-geforce-16gb-gddr7-90yv0lx0-m0na00"),
    ("KaBuM Categoria RTX 5070 Ti", "https://www.kabum.com.br/busca/rtx-5070-ti"),
    ("Pichau Categoria RTX 5070 Ti", "https://www.pichau.com.br/search?q=RTX%205070%20Ti"),
    ("Terabyte Categoria RTX 5070 Ti", "https://www.terabyteshop.com.br/busca?str=RTX+5070+Ti")
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

for name, url in links_to_test:
    try:
        r = requests.get(url, headers=headers, timeout=8, allow_redirects=True)
        print(f"[{r.status_code}] {name} -> URL Final: {r.url}")
    except Exception as e:
        print(f"[Erro] {name}: {e}")
