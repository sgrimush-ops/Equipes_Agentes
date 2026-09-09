"""
GPU Hunter Pro - Interface de Linha de Comando (CLI)
Foco em Alto Desempenho & Viabilidade Financeira: NVIDIA GeForce RTX 5070 Ti (16GB GDDR7)
Lojas: KaBuM! (10x Sem Juros), Pichau (12x Sem Juros) e TerabyteShop (12x Sem Juros).
Análise Centrada no Valor Total a Prazo Sem Juros e Menor Parcela Mensal.
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
    if val is None or val == 0:
        return "R$ 0,00"
    return f"R$ {val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def main():
    seed_sample_history_if_needed()

    print(f"\n{BOLD}{CYAN}=================================================================================================={RESET}")
    print(f"{BOLD}{GREEN}  [*] GPU HUNTER PRO | PARCELAMENTO SEM JUROS & TOTAL A PRAZO - RTX 5070 Ti (16GB GDDR7) {RESET}")
    print(f"{CYAN}  Lojas: Pichau (12x S/ Juros) • TerabyteShop (12x S/ Juros) • KaBuM! (10x S/ Juros){RESET}")
    print(f"{CYAN}  Foco: Viabilidade no Orçamento Mensal & 4K Nativo Ultra (92 FPS Médio){RESET}")
    print(f"{CYAN}=================================================================================================={RESET}\n")

    print("[*] Carregando cotações de parcelamento sem juros e gravando snapshot da RTX 5070 Ti...")
    offers = collect_all_offers(live_scrape=False)
    save_daily_snapshot(offers)
    data = enrich_and_score_offers(offers)
    variations = get_price_variation_stats()

    winner = data.get('winner', {})
    rec = data.get('recommendation', {})
    stats = data.get('model_stats', {}).get('RTX 5070 Ti', {})
    top_by_store = data.get('top_by_store', {})
    limited_promos = data.get('limited_promos', [])

    if winner:
        print(f"\n{BOLD}{YELLOW}[+] CAMPEÃ DE MENOR PARCELA SEM JUROS:{RESET} {BOLD}{GREEN}{winner['gpu_model']} - {winner['brand']}{RESET}")
        print(f"   Título: {winner['title']}")
        print(f"   Loja: {winner['store']} | {BOLD}{GREEN}{winner.get('installments_text')}{RESET}")
        print(f"   Preço Total Sem Juros: {BOLD}{YELLOW}{format_currency(winner['price_card'])}{RESET}")
        print(f"   Custo por FPS Total (1440p Ultra - 145 FPS): {BOLD}R$ {winner['cost_per_fps_1440p']}/FPS{RESET}")
        print(f"   Custo por FPS Total (4K Nativo - 92 FPS): {BOLD}{CYAN}R$ {winner['cost_per_fps_4k']}/FPS{RESET} (apenas R$ {winner.get('monthly_cost_per_fps_4k', 0)}/mês por FPS)")
        print(f"   Score C/B: {BOLD}{GREEN}{winner['cost_benefit_score']}/100{RESET}")
        print(f"   Link: {winner['url']}\n")

    # =========================================================
    # TOP 3 MELHORES OPÇÕES POR LOJA (PARCELAMENTO SEM JUROS)
    # =========================================================
    print(f"{BOLD}{YELLOW}=================================================================================================={RESET}")
    print(f"{BOLD}{YELLOW}🏆 AS 3 MELHORES OPÇÕES SEM JUROS POR LOJA (PICHAU 12X • TERABYTE 12X • KABUM 10X){RESET}")
    print(f"{BOLD}{YELLOW}=================================================================================================={RESET}")

    store_order = [
        ('pichau', '🔴 PICHAU (12x SEM JUROS)'),
        ('terabyte', '🟢 TERABYTESHOP (12x SEM JUROS)'),
        ('kabum', '🟠 KABUM! (10x SEM JUROS)')
    ]

    for sk, store_name in store_order:
        s_data = top_by_store.get(sk, {})
        print(f"\n{BOLD}{CYAN}--- {store_name} ---{RESET}")
        
        items = s_data.get('by_model', {}).get('RTX 5070 Ti', [])
        if items:
            for it in items:
                pos = it.get('rank_label', '#')
                cool = "❄️ 3 Fans" if "Triplo" in it.get('cooling_type', '') else "🌬️ 2 Fans"
                promo = f"{RED}[{it.get('promo_badge')}]{RESET} " if it.get('is_limited_promo') else ""
                print(f"  {BOLD}{pos}{RESET} | {BOLD}{GREEN}{it.get('installments_text')}{RESET} | Total: {YELLOW}{format_currency(it['price_card'])}{RESET} | {cool}")
                print(f"       {promo}{it['title'][:68]}")
                print(f"       Link: {it['url']}")

    # =========================================================
    # COMPARATIVO DE IMPACTO MENSAL NO BOLSO
    # =========================================================
    print(f"\n{BOLD}{CYAN}=================================================================================================={RESET}")
    print(f"{BOLD}{CYAN}💳 COMPARATIVO DE IMPACTO NA RENDA MENSAL (12X vs 10X SEM JUROS):{RESET}")
    print(f"{BOLD}{CYAN}=================================================================================================={RESET}")
    print(f"  • Pichau (12x):      {BOLD}{GREEN}12x de {format_currency(rec.get('pichau_inst', 774.51))} sem juros{RESET}  -> Menor impacto mensal (R$ 774,51/mês)")
    print(f"  • TerabyteShop (12x): {BOLD}{GREEN}12x de {format_currency(rec.get('terabyte_inst', 813.63))} sem juros{RESET}  -> 2ª melhor parcela mensal (R$ 813,63/mês)")
    print(f"  • KaBuM! (10x):       {BOLD}{YELLOW}10x de {format_currency(rec.get('kabum_inst', 929.41))} sem juros{RESET}  -> Quitação mais rápida, porém +R$ {rec.get('diff_monthly_kabum_pichau', 154.90):,.2f}/mês")
    print(f"{'-'*98}")
    print(f"  💡 {BOLD}Veredito:{RESET} A Pichau gera uma folga de {BOLD}{GREEN}R$ {rec.get('diff_monthly_kabum_pichau', 154.90):,.2f} a menos por mês{RESET} no seu fluxo de caixa!")

    # =========================================================
    # MONITOR DE OSCILAÇÃO DO PREÇO TOTAL A PRAZO
    # =========================================================
    print(f"\n{BOLD}{CYAN}[>] MONITOR DE OSCILAÇÃO DO PREÇO TOTAL SEM JUROS (24h, 7d & RECORDE):{RESET}")
    print(f"{'-'*98}")
    print(f"{'Modelo':<16} | {'Total a Prazo':<16} | {'Parcela Mín':<15} | {'Var 24h':<10} | {'Var 7d':<10} | {'Status':<12}")
    print(f"{'-'*98}")

    v = variations.get('RTX 5070 Ti', {})
    if v:
        var24_color = GREEN if v['pct_24h'] < 0 else (RED if v['pct_24h'] > 0 else CYAN)
        var24_str = f"{v['pct_24h']:+.1f}%"
        var7_str = f"{v['pct_7d']:+.1f}%"
        status = "MENOR RECORD" if v['is_at_all_time_low'] else ("Em Queda" if v['trend'] == 'falling' else "Estável")
        inst_min_str = f"12x {format_currency(v.get('min_installment_val', 774.51))}"
        print(f"{'RTX 5070 Ti':<16} | {GREEN}{format_currency(v['current_min_price']):<16}{RESET} | {YELLOW}{inst_min_str:<15}{RESET} | {var24_color}{var24_str:<10}{RESET} | {var7_str:<10} | {YELLOW}{status:<12}{RESET}")
    print(f"{'-'*98}\n")

    print(f"{BOLD}{CYAN}=================================================================================================={RESET}")
    print(f"💡 Para abrir a interface web interativa com os gráficos e simulador de parcelas:")
    print(f"   Execute: {BOLD}python server.py{RESET} ou dê 2 cliques em {BOLD}iniciar.bat{RESET}")
    print(f"{BOLD}{CYAN}=================================================================================================={RESET}\n")

if __name__ == '__main__':
    main()
