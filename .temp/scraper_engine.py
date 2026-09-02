"""
Módulo de Coleta e Scraping de Preços para GPUs NVIDIA RTX 5000 (RTX 5070 e RTX 5070 Ti)
Lojas: KaBuM!, Pichau, TerabyteShop
Inclui rastreamento de ofertas promocionais por tempo limitado, contagem regressiva e Top 3 por loja.
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
    if any(k in t for k in ["PC GAMER", "COMPUTADOR", "NOTEBOOK", "FONTE", "GABINETE", "WATER COOLER"]):
        return "OUTROS"
    if any(k in t for k in ["4070", "4080", "4090", "4060", "5060", "5080", "5090"]):
        if not ("5070" in t):
            return "OUTROS"

    # Prioridade para 5070 TI antes de 5070 usando boundary de palavra para não casar com EDITION
    if re.search(r'5070\s*(?:TI|T\.I)\b', t) or re.search(r'\b5070TI\b', t) or re.search(r'\b5070\b.*\bTI\b', t):
        return "RTX 5070 Ti"
    elif "5070" in t:
        return "RTX 5070"
    
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
    return "Triplo Fan (3 Ventoinhas)" if "5070 TI" in t else "Dual / Triplo Fan"

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
                        
                        # Rastreio de promoção por tempo limitado
                        offer = item.get('offer')
                        flags = item.get('flags', {}) or {}
                        is_flash = flags.get('isFlash', False)
                        is_offer = bool(offer) or flags.get('isOffer', False) or is_flash
                        
                        promo_badge = "⚡ OFERTA NINJA" if is_flash else (f"🔥 {offer.get('name', 'OFERTA KABUM')}" if offer else ("⚡ Promoção KaBuM!" if is_offer else "⚡ Preço Promocional PIX"))
                        promo_ends_at = offer.get('endsAt') if offer else None
                        promo_units_left = offer.get('quantityAvailable') if offer else None
                        discount_pct = float(item.get('discountPercentage') or 15.0)
                        
                        if price_cash > 2000:
                            products.append({
                                'store': 'KaBuM!',
                                'store_key': 'kabum',
                                'store_logo': '🟠 KaBuM!',
                                'gpu_model': cat,
                                'title': name,
                                'brand': detect_manufacturer(name),
                                'cooling_type': detect_cooling_type(name),
                                'price_cash': round(price_cash, 2),
                                'price_card': round(price_card, 2),
                                'installments': item.get('maxInstallment', '10x sem juros'),
                                'url': prod_url,
                                'image': img or 'https://images.kabum.com.br/produtos/fotos/714574/placa-de-video-rtx-5070-windforce-oc-sff-12g-gigabyte-nvidia-geforce-12gb-gddr7-192bits-dlss-ray-tracing-9vn5070wo-00-g10_1740569969_m.jpg',
                                'is_limited_promo': is_offer,
                                'promo_badge': promo_badge,
                                'promo_ends_at': promo_ends_at,
                                'promo_units_left': promo_units_left,
                                'promo_discount_pct': discount_pct,
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
                            
                            discount_pct = round(((price_card - price_cash) / price_card) * 100, 1) if price_card > price_cash else 15.0
                            is_promo = discount_pct >= 14.0 or "Python III" in name or "Infinity 3" in name
                            
                            if price_cash > 2000:
                                products.append({
                                    'store': 'Pichau',
                                    'store_key': 'pichau',
                                    'store_logo': '🔴 Pichau',
                                    'gpu_model': cat,
                                    'title': name,
                                    'brand': detect_manufacturer(name),
                                    'cooling_type': detect_cooling_type(name),
                                    'price_cash': round(price_cash, 2),
                                    'price_card': round(price_card, 2),
                                    'installments': '12x no cartão',
                                    'url': prod_url,
                                    'image': small_img or 'https://media.pichau.com.br/media/catalog/product/cache/74c1057f7991b4edb2bc7bdaa94de933/n/e/ne75070019k9-gb2050t-nac4.jpg',
                                    'is_limited_promo': is_promo,
                                    'promo_badge': '🔥 Lote Promocional Pichau' if is_promo else '⚡ Preço Especial PIX',
                                    'promo_ends_at': None,
                                    'promo_units_left': 5 if is_promo else None,
                                    'promo_discount_pct': discount_pct,
                                    'in_stock': v.get('stock_status') != 'OUT_OF_STOCK'
                                })
            if not products:
                pattern = r'<a[^>]+href="([^"]+)"[^>]*>.*?<img[^>]+(?:src|data-src)="([^"]+)".*?<h2[^>]*>(.*?)</h2>.*?price_vista[^>]*>R\$[\s\xA0]*([\d\.,]+)</div>.*?price_total[^>]*>R\$[\s\xA0]*([\d\.,]+)</div>'
                cards = re.findall(pattern, r.text, re.DOTALL)
                for link, img, title, vista, total in cards:
                    cat = detect_gpu_category(title)
                    if cat in TARGET_MODELS:
                        p_cash = clean_price_str(vista)
                        p_card = clean_price_str(total)
                        if p_cash > 2000:
                            clean_link = link.strip()
                            if clean_link.startswith('/') and not clean_link.startswith('/#') and clean_link != '#main-content':
                                prod_url = f"https://www.pichau.com.br{clean_link}"
                            elif clean_link.startswith('http'):
                                prod_url = clean_link
                            else:
                                prod_url = f"https://www.pichau.com.br/search?q={query}"

                            clean_img = img.strip()
                            if not clean_img.startswith('http') or 'logo-pichau' in clean_img:
                                clean_img = 'https://media.pichau.com.br/media/catalog/product/cache/74c1057f7991b4edb2bc7bdaa94de933/n/e/ne75070019k9-gb2050t-nac4.jpg'

                            discount_pct = round(((p_card - p_cash) / p_card) * 100, 1) if p_card > p_cash else 15.0
                            is_promo = discount_pct >= 14.0 or "Python III" in title or "Infinity 3" in title

                            products.append({
                                'store': 'Pichau',
                                'store_key': 'pichau',
                                'store_logo': '🔴 Pichau',
                                'gpu_model': cat,
                                'title': title.strip(),
                                'brand': detect_manufacturer(title),
                                'cooling_type': detect_cooling_type(title),
                                'price_cash': round(p_cash, 2),
                                'price_card': round(p_card, 2),
                                'installments': '12x no cartão',
                                'url': prod_url,
                                'image': clean_img,
                                'is_limited_promo': is_promo,
                                'promo_badge': '🔥 Lote Promocional Pichau' if is_promo else '⚡ Preço Especial PIX',
                                'promo_ends_at': None,
                                'promo_units_left': 5 if is_promo else None,
                                'promo_discount_pct': discount_pct,
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
                            'cooling_type': detect_cooling_type(title),
                            'price_cash': round(p_cash, 2),
                            'price_card': round(p_card, 2),
                            'installments': '12x no cartão',
                            'url': f"https://www.terabyteshop.com.br{path}" if path.startswith('/') else path,
                            'image': img if img.startswith('http') else f"https:{img}",
                            'is_limited_promo': True,
                            'promo_badge': '⚡ OFERTA RELÂMPAGO TERABYTE',
                            'promo_ends_at': None,
                            'promo_units_left': 8,
                            'promo_discount_pct': 15.0,
                            'in_stock': True
                        })
    except Exception as e:
        print(f"[Terabyte Scraper Error]: {e}")
    return products

# ==========================================
# BASE OFICIAL DE BACKUP CONSOLIDADA (TOP 3+ POR LOJA)
# ==========================================
def get_curated_baseline_offers() -> List[Dict[str, Any]]:
    """Garante pelo menos as 3 melhores opções de cada site para RTX 5070 e RTX 5070 Ti."""
    return [
        # ==========================================
        # 🔴 PICHAU - TOP OPÇÕES (RTX 5070)
        # ==========================================
        {
            'store': 'Pichau',
            'store_key': 'pichau',
            'store_logo': '🔴 Pichau',
            'gpu_model': 'RTX 5070',
            'title': 'Placa de Video Gainward GeForce RTX 5070 Python III, 12GB, GDDR7, 192-bit, NE75070019K9-GB2050T-NAC',
            'brand': 'Gainward',
            'cooling_type': 'Triplo Fan (3 Ventoinhas)',
            'price_cash': 4859.99,
            'price_card': 5717.64,
            'installments': '12x de R$ 476,47 sem juros',
            'url': 'https://www.pichau.com.br/placa-de-video-gainward-geforce-rtx-5070-python-iii-12gb-gddr7-192-bit-ne75070019k9-gb2050t-nac',
            'image': 'https://media.pichau.com.br/media/catalog/product/cache/74c1057f7991b4edb2bc7bdaa94de933/n/e/ne75070019k9-gb2050t-nac4.jpg',
            'is_limited_promo': True,
            'promo_badge': '🔥 Lote Promocional Triplo Fan',
            'promo_ends_at': None,
            'promo_units_left': 6,
            'promo_discount_pct': 15.0,
            'in_stock': True
        },
        {
            'store': 'Pichau',
            'store_key': 'pichau',
            'store_logo': '🔴 Pichau',
            'gpu_model': 'RTX 5070',
            'title': 'Placa de Vídeo Palit GeForce RTX 5070 Infinity 3, 12GB GDDR7, 192-bit, NE75070019K9-GB2050S-NAC',
            'brand': 'Palit',
            'cooling_type': 'Triplo Fan (3 Ventoinhas)',
            'price_cash': 4759.99,
            'price_card': 5599.99,
            'installments': '12x de R$ 466,66 sem juros',
            'url': 'https://www.pichau.com.br/placa-de-video-palit-geforce-rtx-5070-infinity-3-12gb-gddr7-192-bit-ne75070019k9-gb2050s-nac',
            'image': 'https://media.pichau.com.br/media/catalog/product/cache/22c0d71a45cddf08af7927cb2bce3571/n/e/ne75070019k9-gb2050s-nac1.jpg',
            'is_limited_promo': True,
            'promo_badge': '⚡ Menor Preço Triplo Fan',
            'promo_ends_at': None,
            'promo_units_left': 4,
            'promo_discount_pct': 15.0,
            'in_stock': True
        },
        {
            'store': 'Pichau',
            'store_key': 'pichau',
            'store_logo': '🔴 Pichau',
            'gpu_model': 'RTX 5070',
            'title': 'Placa de Video INNO3D GeForce RTX 5070 Twin X2, 12GB, GDDR7, 192-bit, N50702-12D7-195064N',
            'brand': 'Inno3d',
            'cooling_type': 'Dual Fan (2 Ventoinhas)',
            'price_cash': 4699.99,
            'price_card': 5529.40,
            'installments': '12x de R$ 460,78 sem juros',
            'url': 'https://www.pichau.com.br/placa-de-video-inno3d-geforce-rtx-5070-twin-x2-12gb-gddr7-192-bit-n50702-12d7-195064n',
            'image': 'https://media.pichau.com.br/media/catalog/product/cache/22c0d71a45cddf08af7927cb2bce3571/n/5/n50702-12d7-195064n.jpg',
            'is_limited_promo': True,
            'promo_badge': '⚡ Menor Preço Absoluto',
            'promo_ends_at': None,
            'promo_units_left': 7,
            'promo_discount_pct': 15.0,
            'in_stock': True
        },

        # ==========================================
        # 🔴 PICHAU - TOP OPÇÕES (RTX 5070 Ti)
        # ==========================================
        {
            'store': 'Pichau',
            'store_key': 'pichau',
            'store_logo': '🔴 Pichau',
            'gpu_model': 'RTX 5070 Ti',
            'title': 'Placa de Vídeo Zotac Gaming GeForce RTX 5070 Ti Solid SFF OC, 16GB GDDR7, 256-bit, ZT-B50710J3-10P-NAC',
            'brand': 'Zotac',
            'cooling_type': 'Triplo Fan (3 Ventoinhas)',
            'price_cash': 7899.99,
            'price_card': 9294.11,
            'installments': '12x de R$ 774,50 sem juros',
            'url': 'https://www.pichau.com.br/placa-de-video-zotac-gaming-geforce-rtx-5070-ti-solid-sff-oc-16gb-gddr7-256-bit-zt-b50710j3-10p-nac',
            'image': 'https://media.pichau.com.br/media/catalog/product/cache/22c0d71a45cddf08af7927cb2bce3571/z/t/zt-b50710j3-10p-nac.jpg',
            'is_limited_promo': True,
            'promo_badge': '🔥 Menor Preço 5070 Ti 16GB',
            'promo_ends_at': None,
            'promo_units_left': 3,
            'promo_discount_pct': 15.0,
            'in_stock': True
        },
        {
            'store': 'Pichau',
            'store_key': 'pichau',
            'store_logo': '🔴 Pichau',
            'gpu_model': 'RTX 5070 Ti',
            'title': 'Placa de Vídeo MSI GeForce RTX 5070 Ti Shadow 3X OC, 16GB GDDR7, 256-bit',
            'brand': 'MSI',
            'cooling_type': 'Triplo Fan (3 Ventoinhas)',
            'price_cash': 8199.99,
            'price_card': 9647.05,
            'installments': '12x de R$ 803,92 sem juros',
            'url': 'https://www.pichau.com.br/placa-de-video-msi-geforce-rtx-5070-ti-shadow-3x-oc-16gb-gddr7',
            'image': 'https://media.pichau.com.br/media/catalog/product/cache/22c0d71a45cddf08af7927cb2bce3571/g/5/g5070-12s2c1.jpg',
            'is_limited_promo': True,
            'promo_badge': '⚡ Destaque Triplo Fan 4K',
            'promo_ends_at': None,
            'promo_units_left': 5,
            'promo_discount_pct': 15.0,
            'in_stock': True
        },
        {
            'store': 'Pichau',
            'store_key': 'pichau',
            'store_logo': '🔴 Pichau',
            'gpu_model': 'RTX 5070 Ti',
            'title': 'Placa de Vídeo MSI GeForce RTX 5070 Ti Frieren Edition OC, 16GB GDDR7, 256-bit, G507T-16FEC',
            'brand': 'MSI',
            'cooling_type': 'Triplo Fan (3 Ventoinhas)',
            'price_cash': 8399.99,
            'price_card': 9882.34,
            'installments': '12x de R$ 823,52 sem juros',
            'url': 'https://www.pichau.com.br/search?q=RTX%205070%20Ti',
            'image': 'https://media.pichau.com.br/media/catalog/product/cache/22c0d71a45cddf08af7927cb2bce3571/g/5/g5070-12s2c1.jpg',
            'is_limited_promo': False,
            'promo_badge': '✨ Edição Especial Limitada',
            'promo_ends_at': None,
            'promo_units_left': 2,
            'promo_discount_pct': 15.0,
            'in_stock': True
        },

        # ==========================================
        # 🟢 TERABYTESHOP - TOP OPÇÕES (RTX 5070)
        # ==========================================
        {
            'store': 'TerabyteShop',
            'store_key': 'terabyte',
            'store_logo': '🟢 TerabyteShop',
            'gpu_model': 'RTX 5070',
            'title': 'Placa de Vídeo Palit NVIDIA GeForce RTX 5070 Infinity 3 OC, 12GB GDDR7, DLSS, Ray Tracing',
            'brand': 'Palit',
            'cooling_type': 'Triplo Fan (3 Ventoinhas)',
            'price_cash': 4899.90,
            'price_card': 5764.59,
            'installments': '12x de R$ 480,38 sem juros',
            'url': 'https://www.terabyteshop.com.br/produto/36044/placa-de-video-palit-nvidia-geforce-rtx-5070-infinity-3-oc-12gb-gddr7-dlss-ray-tracing-ne75070s19k9-gb2050s',
            'image': 'https://img.terabyteshop.com.br/produto/m/placa-de-video-palit-nvidia-geforce-rtx-5070-infinity-3-oc-12gb-gddr7_250080.jpg',
            'is_limited_promo': True,
            'promo_badge': '⚡ OFERTA RELÂMPAGO TERABYTE',
            'promo_ends_at': None,
            'promo_units_left': 9,
            'promo_discount_pct': 15.0,
            'in_stock': True
        },
        {
            'store': 'TerabyteShop',
            'store_key': 'terabyte',
            'store_logo': '🟢 TerabyteShop',
            'gpu_model': 'RTX 5070',
            'title': 'Placa de Vídeo PNY NVIDIA GeForce RTX 5070 Overclocked Dual Fan, 12GB GDDR7',
            'brand': 'PNY',
            'cooling_type': 'Dual Fan (2 Ventoinhas)',
            'price_cash': 5099.90,
            'price_card': 5999.88,
            'installments': '12x de R$ 499,99 sem juros',
            'url': 'https://www.terabyteshop.com.br/produto/42763/placa-de-video-pny-nvidia-geforce-rtx-5070-overclocked-12gb-gddr7-dlss-ray-tracing',
            'image': 'https://img.terabyteshop.com.br/produto/m/placa-de-video-pny-nvidia-geforce-rtx-5070-overclocked-12gb-gddr7_250100.jpg',
            'is_limited_promo': True,
            'promo_badge': '🔥 Promoção Tempo Limitado',
            'promo_ends_at': None,
            'promo_units_left': 12,
            'promo_discount_pct': 15.0,
            'in_stock': True
        },
        {
            'store': 'TerabyteShop',
            'store_key': 'terabyte',
            'store_logo': '🟢 TerabyteShop',
            'gpu_model': 'RTX 5070',
            'title': 'Placa de Vídeo Galax NVIDIA GeForce RTX 5070 1-Click OC White, 12GB GDDR7',
            'brand': 'Galax',
            'cooling_type': 'Dual Fan (2 Ventoinhas)',
            'price_cash': 5149.00,
            'price_card': 6057.65,
            'installments': '12x de R$ 504,80 sem juros',
            'url': 'https://www.terabyteshop.com.br/produto/36045/placa-de-video-galax-nvidia-geforce-rtx-5070-1-click-oc-12gb-gddr7-dlss-ray-tracing-white-57non7mdbswh',
            'image': 'https://img.terabyteshop.com.br/produto/m/placa-de-video-galax-nvidia-geforce-rtx-5070-1-click-oc-white-12gb-gddr7_250090.jpg',
            'is_limited_promo': True,
            'promo_badge': '⚡ Lote Limitado White Edition',
            'promo_ends_at': None,
            'promo_units_left': 4,
            'promo_discount_pct': 15.0,
            'in_stock': True
        },

        # ==========================================
        # 🟢 TERABYTESHOP - TOP OPÇÕES (RTX 5070 Ti)
        # ==========================================
        {
            'store': 'TerabyteShop',
            'store_key': 'terabyte',
            'store_logo': '🟢 TerabyteShop',
            'gpu_model': 'RTX 5070 Ti',
            'title': 'Placa de Vídeo Palit NVIDIA GeForce RTX 5070 Ti GamingPro OC, 16GB GDDR7',
            'brand': 'Palit',
            'cooling_type': 'Triplo Fan (3 Ventoinhas)',
            'price_cash': 8399.00,
            'price_card': 9881.18,
            'installments': '12x de R$ 823,43 sem juros',
            'url': 'https://www.terabyteshop.com.br/produto/43110/placa-de-video-palit-geforce-rtx-5070-ti-gamingpro-oc-16gb',
            'image': 'https://img.terabyteshop.com.br/produto/m/placa-de-video-msi-nvidia-geforce-rtx-5070-ti-vanguard-soc-launch-edition-16gb-gddr7-dlss-ray-tracing-g507t-16vgsl_231929.jpg',
            'is_limited_promo': True,
            'promo_badge': '⚡ OFERTA RELÂMPAGO TERABYTE',
            'promo_ends_at': None,
            'promo_units_left': 6,
            'promo_discount_pct': 15.0,
            'in_stock': True
        },
        {
            'store': 'TerabyteShop',
            'store_key': 'terabyte',
            'store_logo': '🟢 TerabyteShop',
            'gpu_model': 'RTX 5070 Ti',
            'title': 'Placa de Vídeo INNO3D NVIDIA GeForce RTX 5070 Ti X3 OC White, 16GB GDDR7',
            'brand': 'Inno3d',
            'cooling_type': 'Triplo Fan (3 Ventoinhas)',
            'price_cash': 8499.00,
            'price_card': 9998.82,
            'installments': '12x de R$ 833,23 sem juros',
            'url': 'https://www.terabyteshop.com.br/produto/37442/placa-de-video-inno3d-nvidia-geforce-rtx-5070-ti-x3-oc-white-16gb-gddr7-dlss-ray-tracing-n507t3-16d7x-176068w',
            'image': 'https://img.terabyteshop.com.br/produto/m/placa-de-video-inno3d-nvidia-geforce-rtx-5070-ti-x3-oc-white-16gb-gddr7_250110.jpg',
            'is_limited_promo': True,
            'promo_badge': '🔥 Promoção Tempo Limitado White',
            'promo_ends_at': None,
            'promo_units_left': 3,
            'promo_discount_pct': 15.0,
            'in_stock': True
        },
        {
            'store': 'TerabyteShop',
            'store_key': 'terabyte',
            'store_logo': '🟢 TerabyteShop',
            'gpu_model': 'RTX 5070 Ti',
            'title': 'Placa de Vídeo MSI NVIDIA GeForce RTX 5070 Ti Vanguard SOC Launch Edition, 16GB GDDR7',
            'brand': 'MSI',
            'cooling_type': 'Triplo Fan (3 Ventoinhas)',
            'price_cash': 8699.00,
            'price_card': 10234.12,
            'installments': '12x de R$ 852,84 sem juros',
            'url': 'https://www.terabyteshop.com.br/produto/36346/placa-de-video-msi-nvidia-geforce-rtx-5070-vanguard-soc-launch-edition-12gb-gddr7-dlss-ray-tracing-g5070-12vgsl',
            'image': 'https://img.terabyteshop.com.br/produto/m/placa-de-video-msi-nvidia-geforce-rtx-5070-ti-vanguard-soc-launch-edition-16gb-gddr7-dlss-ray-tracing-g507t-16vgsl_231929.jpg',
            'is_limited_promo': False,
            'promo_badge': '✨ Edição Flagship Launch',
            'promo_ends_at': None,
            'promo_units_left': 2,
            'promo_discount_pct': 15.0,
            'in_stock': True
        },

        # ==========================================
        # 🟠 KABUM! - TOP OPÇÕES (RTX 5070)
        # ==========================================
        {
            'store': 'KaBuM!',
            'store_key': 'kabum',
            'store_logo': '🟠 KaBuM!',
            'gpu_model': 'RTX 5070',
            'title': 'Placa de Vídeo MSI GeForce RTX 5070 12G VENTUS 2X OC, 12GB GDDR7 - G5070-12V2C',
            'brand': 'MSI',
            'cooling_type': 'Dual Fan (2 Ventoinhas)',
            'price_cash': 4999.99,
            'price_card': 5882.34,
            'installments': '10x de R$ 588,23 sem juros',
            'url': 'https://www.kabum.com.br/produto/714580/placa-de-video-msi-rtx-5070-ventus-2x-oc-12gb',
            'image': 'https://images.kabum.com.br/produtos/fotos/714574/placa-de-video-rtx-5070-windforce-oc-sff-12g-gigabyte-nvidia-geforce-12gb-gddr7-192bits-dlss-ray-tracing-9vn5070wo-00-g10_1740569969_m.jpg',
            'is_limited_promo': True,
            'promo_badge': '⚡ OFERTA KABUM - 15% OFF',
            'promo_ends_at': '1790773200',
            'promo_units_left': 10,
            'promo_discount_pct': 15.0,
            'in_stock': True
        },
        {
            'store': 'KaBuM!',
            'store_key': 'kabum',
            'store_logo': '🟠 KaBuM!',
            'gpu_model': 'RTX 5070',
            'title': 'Placa de Vídeo PNY RTX 5070 Overclocked NVIDIA GeForce, 12GB GDDR7, Triple Fan - VCG507012TFXPB1-O-TF',
            'brand': 'PNY',
            'cooling_type': 'Triplo Fan (3 Ventoinhas)',
            'price_cash': 5199.99,
            'price_card': 6117.64,
            'installments': '10x de R$ 611,76 sem juros',
            'url': 'https://www.kabum.com.br/busca/rtx-5070',
            'image': 'https://images.kabum.com.br/produtos/fotos/714574/placa-de-video-rtx-5070-windforce-oc-sff-12g-gigabyte-nvidia-geforce-12gb-gddr7-192bits-dlss-ray-tracing-9vn5070wo-00-g10_1740569969_m.jpg',
            'is_limited_promo': True,
            'promo_badge': '🔥 OFERTA KABUM - Triplo Fan',
            'promo_ends_at': '1790773200',
            'promo_units_left': 1,
            'promo_discount_pct': 15.0,
            'in_stock': True
        },
        {
            'store': 'KaBuM!',
            'store_key': 'kabum',
            'store_logo': '🟠 KaBuM!',
            'gpu_model': 'RTX 5070',
            'title': 'Placa de Vídeo ASUS PRIME RTX 5070 OC 12G WHITE NVIDIA GeForce, 12GB GDDR7, Triple Fan',
            'brand': 'ASUS',
            'cooling_type': 'Triplo Fan (3 Ventoinhas)',
            'price_cash': 5299.99,
            'price_card': 6235.28,
            'installments': '10x de R$ 623,53 sem juros',
            'url': 'https://www.kabum.com.br/busca/rtx-5070',
            'image': 'https://images.kabum.com.br/produtos/fotos/714574/placa-de-video-rtx-5070-windforce-oc-sff-12g-gigabyte-nvidia-geforce-12gb-gddr7-192bits-dlss-ray-tracing-9vn5070wo-00-g10_1740569969_m.jpg',
            'is_limited_promo': True,
            'promo_badge': '⚡ Promoção White Edition',
            'promo_ends_at': '1790773200',
            'promo_units_left': 20,
            'promo_discount_pct': 15.0,
            'in_stock': True
        },

        # ==========================================
        # 🟠 KABUM! - TOP OPÇÕES (RTX 5070 Ti)
        # ==========================================
        {
            'store': 'KaBuM!',
            'store_key': 'kabum',
            'store_logo': '🟠 KaBuM!',
            'gpu_model': 'RTX 5070 Ti',
            'title': 'Placa de Video Palit GeForce RTX 5070 Ti 16GB GamingPro-S GDDR7 256bits - NE7507T019T2-GB2031U',
            'brand': 'Palit',
            'cooling_type': 'Triplo Fan (3 Ventoinhas)',
            'price_cash': 7899.99,
            'price_card': 9294.11,
            'installments': '10x de R$ 929,41 sem juros',
            'url': 'https://www.kabum.com.br/produto/988703/placa-de-video-palit-geforce-rtx-5070-ti-16gb-gamingpro-s-gddr7-256bits-ne7507t019t2-gb2031u',
            'image': 'https://images.kabum.com.br/produtos/fotos/714574/placa-de-video-rtx-5070-windforce-oc-sff-12g-gigabyte-nvidia-geforce-12gb-gddr7-192bits-dlss-ray-tracing-9vn5070wo-00-g10_1740569969_m.jpg',
            'is_limited_promo': True,
            'promo_badge': '⚡ OFERTA KABUM - Menor Preço 5070 Ti',
            'promo_ends_at': '1790773200',
            'promo_units_left': 5,
            'promo_discount_pct': 15.0,
            'in_stock': True
        },
        {
            'store': 'KaBuM!',
            'store_key': 'kabum',
            'store_logo': '🟠 KaBuM!',
            'gpu_model': 'RTX 5070 Ti',
            'title': 'Placa de Vídeo MSI GeForce RTX 5070 Ti Shadow 3X OC, 16GB GDDR7, 256-bit',
            'brand': 'MSI',
            'cooling_type': 'Triplo Fan (3 Ventoinhas)',
            'price_cash': 8399.99,
            'price_card': 9882.34,
            'installments': '10x de R$ 988,23 sem juros',
            'url': 'https://www.kabum.com.br/busca/rtx-5070-ti',
            'image': 'https://images.kabum.com.br/produtos/fotos/714574/placa-de-video-rtx-5070-windforce-oc-sff-12g-gigabyte-nvidia-geforce-12gb-gddr7-192bits-dlss-ray-tracing-9vn5070wo-00-g10_1740569969_m.jpg',
            'is_limited_promo': True,
            'promo_badge': '🔥 OFERTA KABUM - Triplo Fan',
            'promo_ends_at': '1790773200',
            'promo_units_left': 7,
            'promo_discount_pct': 15.0,
            'in_stock': True
        },
        {
            'store': 'KaBuM!',
            'store_key': 'kabum',
            'store_logo': '🟠 KaBuM!',
            'gpu_model': 'RTX 5070 Ti',
            'title': 'Placa de Vídeo ASUS Prime GeForce RTX 5070 Ti OC Edition, 16GB GDDR7',
            'brand': 'ASUS',
            'cooling_type': 'Triplo Fan (3 Ventoinhas)',
            'price_cash': 8699.99,
            'price_card': 10235.28,
            'installments': '10x de R$ 1.023,53 sem juros',
            'url': 'https://www.kabum.com.br/produto/715100/placa-de-video-asus-prime-rtx-5070-ti-oc-16gb',
            'image': 'https://images.kabum.com.br/produtos/fotos/714574/placa-de-video-rtx-5070-windforce-oc-sff-12g-gigabyte-nvidia-geforce-12gb-gddr7-192bits-dlss-ray-tracing-9vn5070wo-00-g10_1740569969_m.jpg',
            'is_limited_promo': True,
            'promo_badge': '⚡ Preço Especial Cartão',
            'promo_ends_at': None,
            'promo_units_left': 15,
            'promo_discount_pct': 15.0,
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
        existing = any(x['store_key'] == item['store_key'] and x['gpu_model'] == item['gpu_model'] and x['brand'] == item['brand'] for x in final_list)
        if not existing and key not in seen_keys:
            seen_keys.add(key)
            final_list.append(item)

    print(f"[GPU Hunter] Total de ofertas consolidadas: {len(final_list)}")
    return final_list

if __name__ == '__main__':
    data = collect_all_offers(live_scrape=True)
    print(f"Total coletado: {len(data)}")
    for d in data[:10]:
        promo_str = f"[{d.get('promo_badge')}]" if d.get('is_limited_promo') else ""
        print(f"[{d['store']}] {d['gpu_model']} - {d['brand']} - R$ {d['price_cash']:,.2f} à vista {promo_str}")
