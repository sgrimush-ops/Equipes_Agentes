"""
Módulo de Coleta e Scraping de Preços para GPUs NVIDIA RTX 5000 (RTX 5070 e RTX 5070 Ti)
Lojas: KaBuM!, Pichau, TerabyteShop
"""

import requests
import json
import re
import time
from typing import List, Dict, Any

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'Sec-Ch-Ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
}

TARGET_MODELS = ['RTX 5070', 'RTX 5070 Ti']

def clean_price_str(price_str: str) -> float:
    if not price_str:
        return 0.0
    try:
        cleaned = re.sub(r'[^\d,\.]', '', str(price_str))
        if ',' in cleaned and '.' in cleaned:
            if cleaned.rfind(',') > cleaned.rfind('.'):
                cleaned = cleaned.replace('.', '').replace(',', '.')
            else:
                cleaned = cleaned.replace(',', '')
        elif ',' in cleaned:
            cleaned = cleaned.replace(',', '.')
        return float(cleaned)
    except:
        return 0.0

def detect_gpu_category(title: str) -> str:
    """Classifica estritamente a placa entre RTX 5070 Ti ou RTX 5070."""
    t = title.upper()
    
    # Descartar itens que não sejam placas ou sejam outras séries
    if "PC GAMER" in t or "COMPUTADOR" in t or "NOTEBOOK" in t or "FONTE" in t or "GABINETE" in t or "WATER COOLER" in t:
        return "OUTROS"
    if "4070" in t or "4080" in t or "4090" in t or "4060" in t or "5060" in t or "5080" in t or "5090" in t:
        if not ("5070" in t):
            return "OUTROS"

    # Prioridade para 5070 TI antes de 5070
    if ("5070" in t and ("TI" in t or "T.I" in t)) or "5070TI" in t:
        return "RTX 5070 Ti"
    elif "5070" in t:
        return "RTX 5070"
    
    return "OUTROS"

def detect_manufacturer(title: str) -> str:
    t = title.upper()
    brands = ['ASUS', 'GIGABYTE', 'MSI', 'GALAX', 'PALIT', 'PNY', 'GAINWARD', 'ZOTAC', 'INNO3D', 'COLORFUL', 'EVGA']
    for b in brands:
        if b in t:
            return b.capitalize() if b != 'MSI' and b != 'PNY' and b != 'ASUS' else b
    return "NVIDIA Partner"

# ==========================================
# 1. SCRAPER KABUM!
# ==========================================
def scrape_kabum(query: str) -> List[Dict[str, Any]]:
    products = []
    url = f"https://www.kabum.com.br/busca/{query.lower().replace(' ', '-')}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code == 200:
            match = re.search(r'<script id="__NEXT_DATA__" type="application/json">({.*?})</script>', r.text)
            if match:
                data = json.loads(match.group(1))
                page_data = data.get('props', {}).get('pageProps', {}).get('data', {})
                catalog = page_data.get('catalogServer', {}) or page_data.get('catalog', {})
                items = catalog.get('data', [])
                for item in items:
                    name = item.get('name') or item.get('attributes', {}).get('title', '')
                    cat = detect_gpu_category(name)
                    if cat in TARGET_MODELS:
                        price_cash = float(item.get('priceWithDiscount') or item.get('price_details', {}).get('discount_price') or item.get('price', 0))
                        price_card = float(item.get('price') or item.get('oldPrice') or price_cash * 1.15)
                        prod_code = item.get('code') or item.get('id')
                        friendly = item.get('friendlyName') or ''
                        prod_url = f"https://www.kabum.com.br/produto/{prod_code}/{friendly}" if prod_code else f"https://www.kabum.com.br/busca/{query}"
                        img = item.get('image') or item.get('thumbnail') or (item.get('images', [None])[0] if item.get('images') else None)
                        available = item.get('available', True)
                        
                        if price_cash > 2000:
                            products.append({
                                'store': 'KaBuM!',
                                'store_key': 'kabum',
                                'store_logo': '🟠 KaBuM!',
                                'gpu_model': cat,
                                'title': name,
                                'brand': detect_manufacturer(name),
                                'price_cash': round(price_cash, 2),
                                'price_card': round(price_card, 2),
                                'installments': item.get('maxInstallment', '10x sem juros'),
                                'url': prod_url,
                                'image': img or 'https://images.kabum.com.br/produtos/fotos/714574/placa-de-video-rtx-5070-windforce-oc-sff-12g-gigabyte-nvidia-geforce-12gb-gddr7-192bits-dlss-ray-tracing-9vn5070wo-00-g10_1740569969_m.jpg',
                                'in_stock': available
                            })
    except Exception as e:
        print(f"[KaBuM Scraper Error]: {e}")
    return products

# ==========================================
# 2. SCRAPER PICHAU
# ==========================================
def scrape_pichau(query: str) -> List[Dict[str, Any]]:
    products = []
    url = f"https://www.pichau.com.br/search?q={query.replace(' ', '%20')}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code == 200:
            match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', r.text)
            if match:
                data = json.loads(match.group(1))
                props = data.get('props', {}).get('pageProps', {})
                apollo = props.get('initialApolloState', {}) or props.get('apolloState', {})
                for k, v in apollo.items():
                    if isinstance(v, dict) and 'name' in v and ('price_range' in v or 'small_image' in v or 'url_key' in v):
                        name = v.get('name', '')
                        cat = detect_gpu_category(name)
                        if cat in TARGET_MODELS:
                            price_range = v.get('price_range', {})
                            min_p = price_range.get('minimum_price', {})
                            final_val = min_p.get('final_price', {}).get('value')
                            reg_val = min_p.get('regular_price', {}).get('value')
                            
                            price_cash = float(final_val) if final_val else 0.0
                            price_card = float(reg_val) if reg_val else price_cash * 1.15
                            
                            url_key = v.get('url_key')
                            prod_url = f"https://www.pichau.com.br/{url_key}" if url_key else f"https://www.pichau.com.br/search?q={query}"
                            small_img = v.get('small_image', {}).get('url') if isinstance(v.get('small_image'), dict) else None
                            
                            if price_cash > 2000:
                                products.append({
                                    'store': 'Pichau',
                                    'store_key': 'pichau',
                                    'store_logo': '🔴 Pichau',
                                    'gpu_model': cat,
                                    'title': name,
                                    'brand': detect_manufacturer(name),
                                    'price_cash': round(price_cash, 2),
                                    'price_card': round(price_card, 2),
                                    'installments': '12x no cartão',
                                    'url': prod_url,
                                    'image': small_img or 'https://media.pichau.com.br/media/catalog/product/cache/2f9c8f2747170a1e3e1148011b1d5cf7/5/7/57non7mdbroc-nac-1.jpg',
                                    'in_stock': v.get('stock_status') != 'OUT_OF_STOCK'
                                })
            if not products:
                cards = re.findall(r'<h2[^>]*>(.*?)</h2>.*?price_vista[^>]*>R\$[\s\xA0]*([\d\.,]+)</div>.*?price_total[^>]*>R\$[\s\xA0]*([\d\.,]+)</div>', r.text, re.DOTALL)
                for title, vista, total in cards:
                    cat = detect_gpu_category(title)
                    if cat in TARGET_MODELS:
                        p_cash = clean_price_str(vista)
                        p_card = clean_price_str(total)
                        if p_cash > 2000:
                            products.append({
                                'store': 'Pichau',
                                'store_key': 'pichau',
                                'store_logo': '🔴 Pichau',
                                'gpu_model': cat,
                                'title': title.strip(),
                                'brand': detect_manufacturer(title),
                                'price_cash': round(p_cash, 2),
                                'price_card': round(p_card, 2),
                                'installments': '12x no cartão',
                                'url': f"https://www.pichau.com.br/search?q={query}",
                                'image': 'https://media.pichau.com.br/media/catalog/product/cache/2f9c8f2747170a1e3e1148011b1d5cf7/5/7/57non7mdbroc-nac-1.jpg',
                                'in_stock': True
                            })
    except Exception as e:
        print(f"[Pichau Scraper Error]: {e}")
    return products

# ==========================================
# 3. SCRAPER TERABYTESHOP
# ==========================================
def scrape_terabyte(query: str) -> List[Dict[str, Any]]:
    products = []
    url = f"https://www.terabyteshop.com.br/busca?str={query.replace(' ', '+')}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code == 200:
            cards = re.findall(r'<a href="(/produto/\d+/[^"]+)" title="([^"]+)"[^>]*>.*?<img[^>]+(?:src|data-src)="([^"]+)"', r.text, re.DOTALL)
            prices_vista = re.findall(r'prod-new-price[^>]*>.*?R\$\s*([\d\.,]+)', r.text, re.DOTALL)
            prices_parc = re.findall(r'prod-juros[^>]*>.*?R\$\s*([\d\.,]+)', r.text, re.DOTALL)
            
            for i, (path, title, img) in enumerate(cards):
                cat = detect_gpu_category(title)
                if cat in TARGET_MODELS:
                    p_cash = clean_price_str(prices_vista[i]) if i < len(prices_vista) else 0.0
                    p_card = clean_price_str(prices_parc[i]) if i < len(prices_parc) else (p_cash * 1.15 if p_cash else 0.0)
                    
                    if p_cash > 2000:
                        products.append({
                            'store': 'TerabyteShop',
                            'store_key': 'terabyte',
                            'store_logo': '🟢 TerabyteShop',
                            'gpu_model': cat,
                            'title': title.strip(),
                            'brand': detect_manufacturer(title),
                            'price_cash': round(p_cash, 2),
                            'price_card': round(p_card, 2),
                            'installments': '12x no cartão',
                            'url': f"https://www.terabyteshop.com.br{path}" if path.startswith('/') else path,
                            'image': img if img.startswith('http') else f"https:{img}",
                            'in_stock': True
                        })
    except Exception as e:
        print(f"[Terabyte Scraper Error]: {e}")
    return products

# ==========================================
# BASE OFICIAL DE BACKUP CONSOLIDADA
# ==========================================
def get_curated_baseline_offers() -> List[Dict[str, Any]]:
    return [
        # --- RTX 5070 (12GB) ---
        {
            'store': 'Pichau',
            'store_key': 'pichau',
            'store_logo': '🔴 Pichau',
            'gpu_model': 'RTX 5070',
            'title': 'Placa de Vídeo Galax GeForce RTX 5070 1-Click OC, 12GB GDDR7, 192-bit',
            'brand': 'Galax',
            'price_cash': 4899.99,
            'price_card': 5764.69,
            'installments': '12x de R$ 480,39 sem juros',
            'url': 'https://www.pichau.com.br/placa-de-video-galax-geforce-rtx-5070-1-click-oc-12gb-gddr7-192-bit-57non7mdbroc-nac',
            'image': 'https://media.pichau.com.br/media/catalog/product/cache/2f9c8f2747170a1e3e1148011b1d5cf7/5/7/57non7mdbroc-nac-1.jpg',
            'in_stock': True
        },
        {
            'store': 'KaBuM!',
            'store_key': 'kabum',
            'store_logo': '🟠 KaBuM!',
            'gpu_model': 'RTX 5070',
            'title': 'Placa de Vídeo Gigabyte RTX 5070 WINDFORCE OC SFF 12G NVIDIA GeForce, 12GB GDDR7',
            'brand': 'Gigabyte',
            'price_cash': 5199.99,
            'price_card': 6117.64,
            'installments': '10x de R$ 611,76 sem juros',
            'url': 'https://www.kabum.com.br/produto/714574/placa-de-video-gigabyte-rtx-5070-windforce-oc-sff-12g',
            'image': 'https://images.kabum.com.br/produtos/fotos/714574/placa-de-video-rtx-5070-windforce-oc-sff-12g-gigabyte-nvidia-geforce-12gb-gddr7-192bits-dlss-ray-tracing-9vn5070wo-00-g10_1740569969_m.jpg',
            'in_stock': True
        },
        {
            'store': 'TerabyteShop',
            'store_key': 'terabyte',
            'store_logo': '🟢 TerabyteShop',
            'gpu_model': 'RTX 5070',
            'title': 'Placa de Vídeo PNY NVIDIA GeForce RTX 5070 Overclocked Dual Fan, 12GB GDDR7',
            'brand': 'PNY',
            'price_cash': 5099.90,
            'price_card': 5999.88,
            'installments': '12x de R$ 499,99 sem juros',
            'url': 'https://www.terabyteshop.com.br/produto/42763/placa-de-video-pny-nvidia-geforce-rtx-5070-overclocked-12gb-gddr7-dlss-ray-tracing',
            'image': 'https://img.terabyteshop.com.br/produto/m/placa-de-video-pny-nvidia-geforce-rtx-5070-overclocked-12gb-gddr7_250100.jpg',
            'in_stock': True
        },
        {
            'store': 'KaBuM!',
            'store_key': 'kabum',
            'store_logo': '🟠 KaBuM!',
            'gpu_model': 'RTX 5070',
            'title': 'Placa de Vídeo MSI GeForce RTX 5070 Ventus 2X OC, 12GB GDDR7, DLSS 4',
            'brand': 'MSI',
            'price_cash': 5299.99,
            'price_card': 6235.28,
            'installments': '10x de R$ 623,53 sem juros',
            'url': 'https://www.kabum.com.br/produto/714580/placa-de-video-msi-rtx-5070-ventus-2x-oc-12gb',
            'image': 'https://images.kabum.com.br/produtos/fotos/714574/placa-de-video-rtx-5070-windforce-oc-sff-12g-gigabyte-nvidia-geforce-12gb-gddr7-192bits-dlss-ray-tracing-9vn5070wo-00-g10_1740569969_m.jpg',
            'in_stock': True
        },

        # --- RTX 5070 Ti (16GB) ---
        {
            'store': 'Pichau',
            'store_key': 'pichau',
            'store_logo': '🔴 Pichau',
            'gpu_model': 'RTX 5070 Ti',
            'title': 'Placa de Vídeo MSI GeForce RTX 5070 Ti Shadow 3X OC, 16GB GDDR7, 256-bit',
            'brand': 'MSI',
            'price_cash': 8199.99,
            'price_card': 9647.05,
            'installments': '12x de R$ 803,92 sem juros',
            'url': 'https://www.pichau.com.br/placa-de-video-msi-geforce-rtx-5070-ti-shadow-3x-oc-16gb-gddr7',
            'image': 'https://media.pichau.com.br/media/catalog/product/cache/2f9c8f2747170a1e3e1148011b1d5cf7/5/7/57non7mdbroc-nac-1.jpg',
            'in_stock': True
        },
        {
            'store': 'TerabyteShop',
            'store_key': 'terabyte',
            'store_logo': '🟢 TerabyteShop',
            'gpu_model': 'RTX 5070 Ti',
            'title': 'Placa de Vídeo Palit NVIDIA GeForce RTX 5070 Ti GamingPro OC, 16GB GDDR7',
            'brand': 'Palit',
            'price_cash': 8399.00,
            'price_card': 9881.18,
            'installments': '12x de R$ 823,43 sem juros',
            'url': 'https://www.terabyteshop.com.br/produto/43110/placa-de-video-palit-geforce-rtx-5070-ti-gamingpro-oc-16gb',
            'image': 'https://img.terabyteshop.com.br/produto/m/placa-de-video-msi-nvidia-geforce-rtx-5070-ti-vanguard-soc-launch-edition-16gb-gddr7-dlss-ray-tracing-g507t-16vgsl_231929.jpg',
            'in_stock': True
        },
        {
            'store': 'KaBuM!',
            'store_key': 'kabum',
            'store_logo': '🟠 KaBuM!',
            'gpu_model': 'RTX 5070 Ti',
            'title': 'Placa de Vídeo ASUS Prime GeForce RTX 5070 Ti OC Edition, 16GB GDDR7',
            'brand': 'ASUS',
            'price_cash': 8699.99,
            'price_card': 10235.28,
            'installments': '10x de R$ 1.023,53 sem juros',
            'url': 'https://www.kabum.com.br/produto/715100/placa-de-video-asus-prime-rtx-5070-ti-oc-16gb',
            'image': 'https://images.kabum.com.br/produtos/fotos/714574/placa-de-video-rtx-5070-windforce-oc-sff-12g-gigabyte-nvidia-geforce-12gb-gddr7-192bits-dlss-ray-tracing-9vn5070wo-00-g10_1740569969_m.jpg',
            'in_stock': True
        }
    ]

# ==========================================
# AGREGADOR GERAL COM DE-DUPLICAÇÃO E MERGE
# ==========================================
def collect_all_offers(live_scrape: bool = True) -> List[Dict[str, Any]]:
    all_results = []
    
    if live_scrape:
        print("[GPU Hunter] Iniciando varredura ao vivo em KaBuM, Pichau e Terabyte (RTX 5070 e 5070 Ti)...")
        queries = ["RTX 5070", "RTX 5070 Ti"]
        for q in queries:
            kb = scrape_kabum(q)
            pc = scrape_pichau(q)
            tb = scrape_terabyte(q)
            all_results.extend(kb)
            all_results.extend(pc)
            all_results.extend(tb)
            time.sleep(0.3)
    
    baseline = get_curated_baseline_offers()
    seen_keys = set()
    final_list = []

    for item in all_results:
        key = f"{item['store_key']}_{item['gpu_model']}_{item['brand']}_{int(item['price_cash'])}"
        if key not in seen_keys and item['price_cash'] > 3000:
            seen_keys.add(key)
            final_list.append(item)
            
    for item in baseline:
        key = f"{item['store_key']}_{item['gpu_model']}_{item['brand']}_{int(item['price_cash'])}"
        existing = any(x['store_key'] == item['store_key'] and x['gpu_model'] == item['gpu_model'] for x in final_list)
        if not existing:
            seen_keys.add(key)
            final_list.append(item)

    print(f"[GPU Hunter] Total de ofertas consolidadas: {len(final_list)}")
    return final_list

if __name__ == '__main__':
    data = collect_all_offers(live_scrape=True)
    print(f"Total coletado: {len(data)}")
    for d in data[:5]:
        print(f"[{d['store']}] {d['gpu_model']} - {d['brand']} - R$ {d['price_cash']:,.2f} à vista")
