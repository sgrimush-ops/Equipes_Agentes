"""
GPU Hunter Pro - Interface de Linha de Comando (CLI)
Foco em Custo-Benefício: RTX 5070 & RTX 5070 Ti nas lojas KaBuM!, Pichau e TerabyteShop.
Inclui: Top 3 Melhores Opções por Loja e Radar de Promoções por Tempo Limitado.
"""

import sys
import os

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from scraper_engine import collect_all_offers
from cost_benefit_engine import enrich_and_score_offers
from history_db import save_daily_snapshot, get_price_variation_stats, seed_sample_history_if_needed

GREEN = '\033[92m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
RED = '\033[91m'
BOLD = '\033[1m'
RESET = '\033[0m'

def format_currency(val):
    return f"R$ {val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def main():
    seed_sample_history_if_needed()

    print(f"\n{BOLD}{CYAN}=================================================================================================={RESET}")
    print(f"{BOLD}{GREEN}  [*] GPU HUNTER PRO | CUSTO-BENEFICIO & HISTORICO DIARIO (RTX 5070 & 5070 Ti) {RESET}")
    print(f"{CYAN}  Lojas: KaBuM!, Pichau, TerabyteShop | Foco em Alto Custo-Beneficio & Triplo Fan{RESET}")
    print(f"{CYAN}=================================================================================================={RESET}\n")

    print("[*] Carregando cotacoes consolidadas e gravando snapshot do dia...")
    offers = collect_all_offers(live_scrape=False)
    save_daily_snapshot(offers)
    data = enrich_and_score_offers(offers)
    variations = get_price_variation_stats()

    winner = data['winner']
    rec = data['recommendation']
    stats = data['model_stats']
    top_by_store = data.get('top_by_store', {})
    limited_promos = data.get('limited_promos', [])

    print(f"\n{BOLD}{YELLOW}[+] CAMPEA DE CUSTO X BENEFICIO DO DIA:{RESET} {BOLD}{GREEN}{winner['gpu_model']} ({winner['brand']}){RESET}")
    print(f"   Loja: {winner['store']} | Preco a Vista: {GREEN}{format_currency(winner['price_cash'])}{RESET}")
    print(f"   Prestacao em 15x (+10% acrescimo): {BOLD}{YELLOW}15x de {format_currency(winner.get('installment_15x_val', 0))}{RESET} (Total: {format_currency(winner.get('price_15x_total', 0))})")
    print(f"   Custo por FPS (1440p): {BOLD}R$ {winner['cost_per_fps_1440p']}/FPS{RESET} (115 FPS)")
    print(f"   Custo por FPS (4K Nativo): {BOLD}{CYAN}R$ {winner['cost_per_fps_4k']}/FPS{RESET} (72 FPS)")
    print(f"   Link: {winner['url']}\n")

    # =========================================================
    # TOP 3 MELHORES OPÇÕES POR LOJA
    # =========================================================
    print(f"{BOLD}{YELLOW}=================================================================================================={RESET}")
    print(f"{BOLD}{YELLOW}🏆 AS 3 MELHORES OPÇÕES DE CADA SITE (PICHAU • TERABYTE • KABUM){RESET}")
    print(f"{BOLD}{YELLOW}=================================================================================================={RESET}")

    store_order = [
        ('pichau', '🔴 PICHAU'),
        ('terabyte', '🟢 TERABYTESHOP'),
        ('kabum', '🟠 KABUM!')
    ]

    for sk, store_name in store_order:
        s_data = top_by_store.get(sk, {})
        print(f"\n{BOLD}{CYAN}--- {store_name} ---{RESET}")
        
        for model in ['RTX 5070', 'RTX 5070 Ti']:
            items = s_data.get('by_model', {}).get(model, [])
            if items:
                print(f"  {BOLD}[{model}]{RESET}")
                for it in items:
                    pos = it.get('rank_label', '#')
                    cool = "❄️ 3 Fans" if "Triplo" in it.get('cooling_type', '') else "🌬️ 2 Fans"
                    promo = f"{RED}[{it.get('promo_badge')}]{RESET} " if it.get('is_limited_promo') else ""
                    print(f"    {BOLD}{pos}{RESET} | {GREEN}{format_currency(it['price_cash'])}{RESET} ({it['installments']}) | {cool} | {promo}{it['title'][:65]}")
                    print(f"         Link: {it['url']}")

    # =========================================================
    # RADAR DE PROMOÇÕES POR TEMPO LIMITADO
    # =========================================================
    if limited_promos:
        print(f"\n{BOLD}{RED}=================================================================================================={RESET}")
        print(f"{BOLD}{RED}⚡ RADAR DE PROMOÇÕES POR TEMPO LIMITADO & OFERTAS RELÂMPAGO ({len(limited_promos)} ATIVAS){RESET}")
        print(f"{BOLD}{RED}=================================================================================================={RESET}")
        for p in limited_promos[:6]:
            cool = "❄️ Triplo Fan" if "Triplo" in p.get('cooling_type', '') else "🌬️ Dual Fan"
            units = f" | Restam: {p.get('promo_units_left')} un." if p.get('promo_units_left') else ""
            print(f"  • [{p['store']}] {BOLD}{p.get('promo_badge', 'OFERTA')}{RESET}{units}")
            print(f"    {p['title']}")
            print(f"    Preço à Vista: {GREEN}{format_currency(p['price_cash'])}{RESET} | 15x de {YELLOW}{format_currency(p.get('installment_15x_val', 0))}{RESET} | {cool}")
            print(f"    Link: {p['url']}\n")

    # =========================================================
    # MONITOR DE OSCILAÇÃO
    # =========================================================
    print(f"{BOLD}{CYAN}[>] MONITOR DE OSCILACAO DIARIA (24h, 7d & RECORDE HISTORICO):{RESET}")
    print(f"{'-'*95}")
    print(f"{'Modelo':<14} | {'Preco Hoje':<14} | {'Var 24h':<12} | {'Var 7d':<12} | {'Menor Historico':<16} | {'Status':<10}")
    print(f"{'-'*95}")

    for model in ['RTX 5070', 'RTX 5070 Ti']:
        v = variations.get(model, {})
        if v:
            var24_color = GREEN if v['pct_24h'] < 0 else (RED if v['pct_24h'] > 0 else CYAN)
            var24_str = f"{v['pct_24h']:+.1f}%"
            var7_str = f"{v['pct_7d']:+.1f}%"
            status = "RECORD LOW!" if v['is_at_all_time_low'] else ("Em Queda" if v['trend'] == 'falling' else "Estavel")
            print(f"{model:<14} | {GREEN}{format_currency(v['current_min_price']):<14}{RESET} | {var24_color}{var24_str:<12}{RESET} | {var7_str:<12} | {format_currency(v['all_time_low']):<16} | {YELLOW}{status:<10}{RESET}")
    print(f"{'-'*95}\n")

    print(f"{BOLD}{CYAN}=================================================================================================={RESET}")
    print(f"💡 Para abrir a interface web com o painel visual completo e simuladores interativos:")
    print(f"   Execute: {BOLD}python server.py{RESET} ou de 2 cliques em {BOLD}iniciar.bat{RESET}")
    print(f"{BOLD}{CYAN}=================================================================================================={RESET}\n")

if __name__ == '__main__':
    main()
