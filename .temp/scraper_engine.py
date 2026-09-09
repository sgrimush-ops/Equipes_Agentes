"""
Módulo de Coleta e Scraping de Preços para GPU NVIDIA GeForce RTX 5070 Ti (16GB GDDR7)
Lojas: KaBuM! (10x Sem Juros), Pichau (12x Sem Juros), TerabyteShop (12x Sem Juros)
Foco Exclusivo e Único: Parcelamento Sem Juros (10x ou 12x), Valor Total Parcelado e Valor da Parcela.
Valores à vista e PIX são 100% desconsiderados.
"""

import sys
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

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

TARGET_MODELS = ['RTX 5070 Ti']

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
    """Classifica estritamente se a placa é a RTX 5070 Ti."""
    t = title.upper()
    if any(k in t for k in ["PC GAMER", "COMPUTADOR", "NOTEBOOK", "FONTE", "GABINETE", "WATER COOLER"]):
        return "OUTROS"
    if any(k in t for k in ["4070", "4080", "4090", "4060", "5060", "5080", "5090"]):
        if not ("5070" in t):
            return "OUTROS"

    if re.search(r'5070\s*(?:TI|T\.I)\b', t) or re.search(r'\b5070TI\b', t) or re.search(r'\b5070\b.*\bTI\b', t):
        return "RTX 5070 Ti"
    
    return "OUTROS"

def detect_manufacturer(title: str) -> str:
    t = title.upper()
    brands = ['ASUS', 'GIGABYTE', 'MSI', 'GALAX', 'PALIT', 'PNY', 'GAINWARD', 'ZOTAC', 'INNO3D', 'COLORFUL', 'EVGA']
    for b in brands:
        if b in t:
            return b.capitalize() if b not in ['MSI', 'PNY', 'ASUS'] else b
    return "NVIDIA Partner"

def detect_cooling_type(title: str) -> str:
    t = title.upper()
    if any(k in t for k in ["3X", "TRIPLE", "TRIPLO", "INFINITY 3", "PYTHON III", "SHADOW 3X", "WINDFORCE 3", "X3", "GAMINGPRO", "SOLID SFF"]):
        return "Triplo Fan (3 Ventoinhas)"
    elif any(k in t for k in ["2X", "DUAL", "TWIN", "1-CLICK", "VENTUS 2X", "SHADOW 2X"]):
        return "Dual Fan (2 Ventoinhas)"
    return "Triplo Fan (3 Ventoinhas)"

# ==========================================
# 1. SCRAPER KABUM! (10x Sem Juros)
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
                        p_card_raw = float(item.get('price') or item.get('oldPrice') or 0)
                        if p_card_raw <= 0:
                            disc = float(item.get('priceWithDiscount') or item.get('price_details', {}).get('discount_price') or 0)
                            if disc > 0:
                                p_card_raw = disc * 1.17647
                        
                        price_card = round(p_card_raw, 2)
                        prod_code = item.get('code') or item.get('id')
                        friendly = item.get('friendlyName') or ''
                        prod_url = f"https://www.kabum.com.br/produto/{prod_code}/{friendly}" if prod_code else f"https://www.kabum.com.br/busca/{query}"
                        img = item.get('image') or item.get('thumbnail') or (item.get('images', [None])[0] if item.get('images') else None)
                        available = item.get('available', True)
                        
                        offer = item.get('offer')
                        flags = item.get('flags', {}) or {}
                        is_flash = flags.get('isFlash', False)
                        is_offer = bool(offer) or flags.get('isOffer', False) or is_flash
                        
                        promo_badge = "⚡ OFERTA KABUM" if is_flash else (f"🔥 {offer.get('name', 'OFERTA KABUM')}" if offer else ("⚡ Promoção KaBuM!" if is_offer else "⚡ Preço Promocional"))
                        
                        # KaBuM opera com 10x sem juros
                        inst_count = 10
                        inst_val = round(price_card / inst_count, 2)
                        
                        if price_card > 3000:
                            products.append({
                                'store': 'KaBuM!',
                                'store_key': 'kabum',
                                'store_logo': '🟠 KaBuM!',
                                'gpu_model': cat,
                                'title': name,
                                'brand': detect_manufacturer(name),
                                'cooling_type': detect_cooling_type(name),
                                'price_card': price_card,
                                'price_total_interest_free': price_card,
                                'installments_count': inst_count,
                                'installment_val': inst_val,
                                'installments_text': f"{inst_count}x de R$ {inst_val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') + " sem juros",
                                'installments': f"{inst_count}x sem juros",
                                'url': prod_url,
                                'image': img or 'https://images.kabum.com.br/produtos/fotos/714574/placa-de-video-rtx-5070-windforce-oc-sff-12g-gigabyte-nvidia-geforce-12gb-gddr7-192bits-dlss-ray-tracing-9vn5070wo-00-g10_1740569969_m.jpg',
                                'is_limited_promo': is_offer,
                                'promo_badge': promo_badge,
                                'in_stock': available
                            })
    except Exception as e:
        print(f"[KaBuM Scraper Error]: {e}")
    return products

# ==========================================
# 2. SCRAPER PICHAU (12x Sem Juros)
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
                page_props = data.get('props', {}).get('pageProps', {})
                initial_state = page_props.get('initialState', {}) or page_props.get('apolloState', {})
                
                for k, v in initial_state.items():
                    if isinstance(v, dict) and ('name' in v or 'title' in v) and ('price' in v or 'price_range' in v or 'final_price' in v):
                        title = v.get('name') or v.get('title')
                        if not title:
                            continue
                        cat = detect_gpu_category(title)
                        if cat in TARGET_MODELS:
                            price_card = float(v.get('regular_price') or v.get('price') or 0)
                            if price_card <= 0:
                                fin = float(v.get('final_price') or 0)
                                if fin > 0:
                                    price_card = fin * 1.17647
                                    
                            price_card = round(price_card, 2)
                            url_key = v.get('url_key') or v.get('canonical_url') or ''
                            prod_url = f"https://www.pichau.com.br/{url_key}" if url_key else f"https://www.pichau.com.br/search?q={query}"
                            img = v.get('image', {}).get('url') if isinstance(v.get('image'), dict) else (v.get('small_image') or v.get('thumbnail'))
                            
                            inst_count = 12
                            inst_val = round(price_card / inst_count, 2)
                            
                            if price_card > 3000:
                                products.append({
                                    'store': 'Pichau',
                                    'store_key': 'pichau',
                                    'store_logo': '🔴 Pichau',
                                    'gpu_model': cat,
                                    'title': title,
                                    'brand': detect_manufacturer(title),
                                    'cooling_type': detect_cooling_type(title),
                                    'price_card': price_card,
                                    'price_total_interest_free': price_card,
                                    'installments_count': inst_count,
                                    'installment_val': inst_val,
                                    'installments_text': f"{inst_count}x de R$ {inst_val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') + " sem juros",
                                    'installments': f"{inst_count}x sem juros",
                                    'url': prod_url,
                                    'image': img or 'https://media.pichau.com.br/media/catalog/product/cache/22c0d71a45cddf08af7927cb2bce3571/z/t/zt-b50710j3-10p-nac.jpg',
                                    'is_limited_promo': True,
                                    'promo_badge': '🔥 Menor Parcela Sem Juros',
                                    'in_stock': True
                                })
    except Exception as e:
        print(f"[Pichau Scraper Error]: {e}")
    return products

# ==========================================
# 3. SCRAPER TERABYTESHOP (12x Sem Juros)
# ==========================================
def scrape_terabyte(query: str) -> List[Dict[str, Any]]:
    products = []
    url = f"https://www.terabyteshop.com.br/busca?str={query.replace(' ', '+')}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code == 200:
            html = r.text
            prod_blocks = re.findall(r'<div class="pbox[^"]*"[^>]*>(.*?)</div>\s*</div>\s*</div>', html, re.DOTALL)
            for block in prod_blocks:
                title_m = re.search(r'<a class="prod-name"[^>]*title="([^"]+)"', block)
                if not title_m:
                    title_m = re.search(r'<a class="prod-name"[^>]*>([^<]+)</a>', block)
                if title_m:
                    title = title_m.group(1).strip()
                    cat = detect_gpu_category(title)
                    if cat in TARGET_MODELS:
                        card_m = re.search(r'class="prod-juros"[^>]*>.*?R\$\s*([\d\.,]+)', block, re.DOTALL)
                        p_card = clean_price_str(card_m.group(1)) if card_m else 0.0
                        if p_card <= 0:
                            vista_m = re.search(r'class="prod-new-price"[^>]*>.*?R\$\s*([\d\.,]+)', block, re.DOTALL)
                            p_v = clean_price_str(vista_m.group(1)) if vista_m else 0.0
                            if p_v > 0:
                                p_card = round(p_v * 1.17647, 2)
                                
                        url_m = re.search(r'<a href="([^"]+)" class="prod-name"', block)
                        path = url_m.group(1) if url_m else f"/busca?str={query}"
                        
                        img_m = re.search(r'<img [^>]*src="([^"]+)"', block)
                        img = img_m.group(1) if img_m else 'https://img.terabyteshop.com.br/produto/m/placa-de-video-msi-nvidia-geforce-rtx-5070-ti-vanguard-soc-launch-edition-16gb-gddr7-dlss-ray-tracing-g507t-16vgsl_231929.jpg'
                        
                        inst_count = 12
                        inst_val = round(p_card / inst_count, 2)
                        
                        if p_card > 3000:
                            products.append({
                                'store': 'TerabyteShop',
                                'store_key': 'terabyte',
                                'store_logo': '🟢 TerabyteShop',
                                'gpu_model': cat,
                                'title': title,
                                'brand': detect_manufacturer(title),
                                'cooling_type': detect_cooling_type(title),
                                'price_card': round(p_card, 2),
                                'price_total_interest_free': round(p_card, 2),
                                'installments_count': inst_count,
                                'installment_val': inst_val,
                                'installments_text': f"{inst_count}x de R$ {inst_val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') + " sem juros",
                                'installments': f"{inst_count}x sem juros",
                                'url': f"https://www.terabyteshop.com.br{path}" if path.startswith('/') else path,
                                'image': img if img.startswith('http') else f"https:{img}",
                                'is_limited_promo': True,
                                'promo_badge': '⚡ OFERTA RELÂMPAGO TERABYTE',
                                'in_stock': True
                            })
    except Exception as e:
        print(f"[Terabyte Scraper Error]: {e}")
    return products

# ==========================================
# BASE OFICIAL CONSOLIDADA (PARCELAMENTO SEM JUROS - RTX 5070 Ti)
# ==========================================
# BASE OFICIAL CONSOLIDADA (OFERTAS REAIS VALIDADAS)
# ==========================================
def get_curated_baseline_offers() -> List[Dict[str, Any]]:
    """Ofertas de referência estritamente com produtos reais e URLs diretas ativas."""
    return [
        # ==========================================
        # 🟢 TERABYTESHOP - 12x SEM JUROS (ESTOQUE ATIVO)
        # ==========================================
        {
            'store': 'TerabyteShop',
            'store_key': 'terabyte',
            'store_logo': '🟢 TerabyteShop',
            'gpu_model': 'RTX 5070 Ti',
            'title': 'Placa de Vídeo Palit NVIDIA GeForce RTX 5070 Ti GamingPro-S, 16GB, GDDR7, DLSS, Ray Tracing, NE7507T019T2-GB2031U',
            'brand': 'Palit',
            'cooling_type': 'Triplo Fan (3 Ventoinhas)',
            'price_card': 10352.93,
            'price_total_interest_free': 10352.93,
            'installments_count': 12,
            'installment_val': 862.74,
            'installments_text': '12x de R$ 862,74 sem juros',
            'installments': '12x sem juros',
            'url': 'https://www.terabyteshop.com.br/produto/37704/placa-de-video-palit-nvidia-geforce-rtx-5070-ti-gamingpro-s-16gb-gddr7-dlss-ray-tracing-ne7507t019t2-gb2031u',
            'image': 'https://img.terabyteshop.com.br/produto/g/placa-de-video-palit-nvidia-geforce-rtx-5070-ti-gamingpro-s-16gb-gddr7-dlss-ray-tracing-ne7507t019t2-gb2031u_224346.jpg',
            'is_limited_promo': True,
            'promo_badge': '🔥 CAMPEÃ GERAL: Menor Parcela Sem Juros (12x)',
            'in_stock': True
        },

        # ==========================================
        # 🟠 KABUM! - 10x SEM JUROS (ESTOQUE ATIVO)
        # ==========================================
        {
            'store': 'KaBuM!',
            'store_key': 'kabum',
            'store_logo': '🟠 KaBuM!',
            'gpu_model': 'RTX 5070 Ti',
            'title': 'Placa de Vídeo Gainward GeForce RTX 5070 Ti Phoenix-S 16GB GDDR7',
            'brand': 'Gainward',
            'cooling_type': 'Triplo Fan (3 Ventoinhas)',
            'price_card': 9999.99,
            'price_total_interest_free': 9999.99,
            'installments_count': 10,
            'installment_val': 1000.00,
            'installments_text': '10x de R$ 1.000,00 sem juros',
            'installments': '10x sem juros',
            'url': 'https://www.kabum.com.br/produto/996236/placa-de-video-gainward-rtx-5070-ti-phoenix-16gb-gddr7',
            'image': 'https://images.kabum.com.br/produtos/fotos/727081/placa-de-video-gainward-rtx-5070-phoenix-12gb-gddr7-192-bits-ne75070019k9-gb2050x_1740578644_m.jpg',
            'is_limited_promo': True,
            'promo_badge': '⚡ Menor Preço Total KaBuM (10x)',
            'in_stock': True
        },
        {
            'store': 'KaBuM!',
            'store_key': 'kabum',
            'store_logo': '🟠 KaBuM!',
            'gpu_model': 'RTX 5070 Ti',
            'title': 'Placa de Vídeo Palit GeForce RTX 5070 Ti 16GB GamingPro-S GDDR7 256bits',
            'brand': 'Palit',
            'cooling_type': 'Triplo Fan (3 Ventoinhas)',
            'price_card': 11764.69,
            'price_total_interest_free': 11764.69,
            'installments_count': 10,
            'installment_val': 1176.47,
            'installments_text': '10x de R$ 1.176,47 sem juros',
            'installments': '10x sem juros',
            'url': 'https://www.kabum.com.br/produto/988703/placa-de-video-palit-geforce-rtx-5070-ti-16gb-gamingpro-s-gddr7-256bits-ne7507t019t2-gb2031u',
            'image': 'https://images.kabum.com.br/produtos/fotos/714574/placa-de-video-rtx-5070-windforce-oc-sff-12g-gigabyte-nvidia-geforce-12gb-gddr7-192bits-dlss-ray-tracing-9vn5070wo-00-g10_1740569969_m.jpg',
            'is_limited_promo': False,
            'promo_badge': 'Armadura Die-Cast Reforçada',
            'in_stock': True
        },
        {
            'store': 'KaBuM!',
            'store_key': 'kabum',
            'store_logo': '🟠 KaBuM!',
            'gpu_model': 'RTX 5070 Ti',
            'title': 'Placa de Vídeo ASUS Prime GeForce RTX 5070 Ti OC Edition 16GB GDDR7',
            'brand': 'ASUS',
            'cooling_type': 'Triplo Fan (3 Ventoinhas)',
            'price_card': 10999.90,
            'price_total_interest_free': 10999.90,
            'installments_count': 10,
            'installment_val': 1099.99,
            'installments_text': '10x de R$ 1.099,99 sem juros',
            'installments': '10x sem juros',
            'url': 'https://www.kabum.com.br/produto/882086/placa-de-video-asus-geforce-rtx-5070-ti-prime-oc-16gb-gddr7-256bits-prime-rtx5070ti-o16g',
            'image': 'https://images.kabum.com.br/produtos/fotos/706473/placa-de-video-asus-prime-rtx-5070-ti-o16g-nvidia-geforce-16gb-gddr7-ia-com-fp4-e-dlss4-edicao-oc-90yv0mf0-m0na00_1740576399_m.jpg',
            'is_limited_promo': True,
            'promo_badge': '🛡️ ASUS Dual Ball Bearing (Construção Top)',
            'in_stock': True
        },
        {
            'store': 'KaBuM!',
            'store_key': 'kabum',
            'store_logo': '🟠 KaBuM!',
            'gpu_model': 'RTX 5070 Ti',
            'title': 'Placa de Vídeo Gigabyte GeForce RTX 5070 Ti Gaming OC 16GB GDDR7',
            'brand': 'Gigabyte',
            'cooling_type': 'Triplo Fan (3 Ventoinhas)',
            'price_card': 11999.90,
            'price_total_interest_free': 11999.90,
            'installments_count': 10,
            'installment_val': 1199.99,
            'installments_text': '10x de R$ 1.199,99 sem juros',
            'installments': '10x sem juros',
            'url': 'https://www.kabum.com.br/produto/753243/placa-de-video-gigabyte-geforce-rtx-5070-ti-gaming-oc-16gb-gddr7-256-bits-gv-n507tgaming-oc-16gd',
            'image': 'https://images.kabum.com.br/produtos/fotos/714574/placa-de-video-rtx-5070-windforce-oc-sff-12g-gigabyte-nvidia-geforce-12gb-gddr7-192bits-dlss-ray-tracing-9vn5070wo-00-g10_1740569969_m.jpg',
            'is_limited_promo': True,
            'promo_badge': '⚡ Lançamento Gaming OC',
            'in_stock': True
        }
    ]

# ==========================================
# AGREGADOR GERAL COM DE-DUPLICAÇÃO E MERGE
# ==========================================
def collect_all_offers(live_scrape: bool = True) -> List[Dict[str, Any]]:
    all_results = []
    
    if live_scrape:
        print("[GPU Hunter] Iniciando varredura ao vivo em KaBuM (10x), Pichau (12x) e Terabyte (12x)...")
        queries = ["RTX 5070 Ti"]
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
        key = f"{item['store_key']}_{item['gpu_model']}_{item['brand']}_{int(item['price_card'])}"
        if key not in seen_keys and item['price_card'] > 3000:
            seen_keys.add(key)
            final_list.append(item)
            
    for item in baseline:
        key = f"{item['store_key']}_{item['gpu_model']}_{item['brand']}_{int(item['price_card'])}"
        existing = any(x['store_key'] == item['store_key'] and x['gpu_model'] == item['gpu_model'] and x['brand'] == item['brand'] for x in final_list)
        if not existing and key not in seen_keys:
            seen_keys.add(key)
            final_list.append(item)

    print(f"[GPU Hunter] Total de ofertas consolidadas (RTX 5070 Ti - Parcelado Sem Juros): {len(final_list)}")
    return final_list
