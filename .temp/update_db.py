import sys
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from scraper_engine import collect_all_offers
from history_db import init_db, save_daily_snapshot, seed_sample_history_if_needed

init_db()
offers = collect_all_offers(live_scrape=True)
print(f"Total de ofertas coletadas: {len(offers)}")
for o in offers:
    print(f"- [{o['store']}] {o['title']} | Total Sem Juros: R$ {o['price_card']:.2f} | Parcela: {o['installments_text']} | URL: {o['url']}")

save_daily_snapshot(offers)
seed_sample_history_if_needed()
print("Banco de dados atualizado com sucesso!")
