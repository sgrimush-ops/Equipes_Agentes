import requests
import json

r = requests.get('http://127.0.0.1:5000/api/gpus', timeout=5)
res = r.json()
print("Status API:", res.get('status'))
data = res.get('data', {})
offers = data.get('offers', [])
print("Total de ofertas:", len(offers))
top = data.get('top_by_store', {})
for k, v in top.items():
    store_offers = v.get('by_model', {}).get('RTX 5070 Ti', [])
    print(f"\nLoja {k.upper()} ({v.get('store_name')}): {len(store_offers)} ofertas ativas")
    for o in store_offers:
        print(f"  - [{o['rank_label']}] {o['title']} | R$ {o['price_card']:.2f} | {o['installments_text']} | URL: {o['url']}")
