import requests
import json
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}

print("=== VERIFICANDO LINKS REAIS PICHAU ===")
try:
    url = "https://www.pichau.com.br/hardware/placa-de-video?fabricante_gpu=5561" # NVIDIA
    r = requests.get(url, headers=headers, timeout=12)
    print("Pichau category status:", r.status_code)
    m = re.findall(r'<a href="([^"]+)" class="MuiTypography-root[^"]*"[^>]*>([^<]+)</a>', r.text)
    print("Pichau links encontrados:", len(m))
    for link, title in m[:10]:
        print(f"Pichau: {title} -> https://www.pichau.com.br{link}")
except Exception as e:
    print("Erro Pichau:", e)

print("\n=== VERIFICANDO LINKS REAIS TERABYTE ===")
try:
    url = "https://www.terabyteshop.com.br/hardware/placas-de-video/nvidia-geforce"
    r = requests.get(url, headers=headers, timeout=12)
    print("Terabyte category status:", r.status_code)
    # Procurar tags de produto na Terabyte
    items = re.findall(r'<a class="prod-name" href="([^"]+)"[^>]*title="([^"]+)"', r.text)
    if not items:
        items = re.findall(r'<a class="prod-name" href="([^"]+)"[^>]*>([^<]+)</a>', r.text)
    print("Terabyte produtos encontrados:", len(items))
    for link, title in items[:10]:
        print(f"Terabyte: {title} -> {link}")
except Exception as e:
    print("Erro Terabyte:", e)
