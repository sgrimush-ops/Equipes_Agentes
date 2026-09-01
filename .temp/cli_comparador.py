"""
GPU Hunter Pro - Interface de Linha de Comando (CLI)
Foco em Custo-Benefício: RTX 5070 & RTX 5070 Ti nas lojas KaBuM!, Pichau e TerabyteShop.
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

    print(f"\n{BOLD}{CYAN}========================================================================================{RESET}")
    print(f"{BOLD}{GREEN}  [*] GPU HUNTER PRO | CUSTO-BENEFICIO & HISTORICO DIARIO (RTX 5070 & 5070 Ti) {RESET}")
    print(f"{CYAN}  Lojas: KaBuM!, Pichau, TerabyteShop | Foco em Alto Custo-Beneficio{RESET}")
    print(f"{CYAN}========================================================================================{RESET}\n")

    print("[*] Carregando cotacoes consolidadas e gravando snapshot do dia...")
    offers = collect_all_offers(live_scrape=False)
    save_daily_snapshot(offers)
    data = enrich_and_score_offers(offers)
    variations = get_price_variation_stats()

    winner = data['winner']
    rec = data['recommendation']
    stats = data['model_stats']

    print(f"\n{BOLD}{YELLOW}[+] CAMPEA DE CUSTO X BENEFICIO DO DIA:{RESET} {BOLD}{GREEN}{winner['gpu_model']} ({winner['brand']}){RESET}")
    print(f"   Loja: {winner['store']} | Preco a Vista: {GREEN}{format_currency(winner['price_cash'])}{RESET}")
    print(f"   Prestacao em 15x (+10% acrescimo): {BOLD}{YELLOW}15x de {format_currency(winner.get('installment_15x_val', 0))}{RESET} (Total: {format_currency(winner.get('price_15x_total', 0))})")
    print(f"   Custo por FPS (1440p): {BOLD}R$ {winner['cost_per_fps_1440p']}/FPS{RESET} (115 FPS)")
    print(f"   Custo por FPS (4K Nativo): {BOLD}{CYAN}R$ {winner['cost_per_fps_4k']}/FPS{RESET} (72 FPS)")
    print(f"   Link: {winner['url']}\n")

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

    print(f"{BOLD}{CYAN}[>] COMPARATIVO DIRETO (1440p, 4K NATIVO & PLANO 15x):{RESET}")
    print(f"{'-'*115}")
    print(f"{'Modelo':<14} | {'A Vista (PIX)':<14} | {'Plano 15x (+10%)':<19} | {'FPS 1440p':<10} | {'R$/FPS 1440p':<14} | {'FPS 4K':<8} | {'R$/FPS 4K':<12} | {'VRAM':<6}")
    print(f"{'-'*115}")
    
    for model in ['RTX 5070', 'RTX 5070 Ti']:
        st = stats.get(model, {})
        if st:
            vram_str = "12GB" if model == 'RTX 5070' else "16GB"
            print(f"{model:<14} | {GREEN}{format_currency(st['min_price']):<14}{RESET} | {YELLOW}{st['min_installment_15x_text']:<19}{RESET} | {st['avg_fps_1440p']:<10} | R$ {st['cost_per_fps_1440p']:<11} | {st['avg_fps_4k']:<8} | {CYAN}R$ {st['cost_per_fps_4k']:<9}{RESET} | {vram_str:<6}")
    print(f"{'-'*115}\n")

    print(f"{BOLD}{YELLOW}[*] PARECER TECNICO & PORQUE DA ESCOLHA:{RESET}")
    for item in rec.get('detailed_points', []):
        print(f"\n{BOLD}{CYAN}• {item['category']} - {item['model']}{RESET}")
        print(f"  Referencia a Vista: {item['price_ref']}")
        print(f"  {YELLOW}Prestacao 15x: {item.get('price_15x', '')}{RESET}")
        print(f"  Rendimento: 1440p: {item['fps_1440p']} ({item['cost_fps_1440p']}) | 4K Nativo: {item['fps_4k']} ({item['cost_fps_4k']})")
        print(f"  {item['why_choose']}")
        print(f"  {GREEN}Vantagens:{RESET} {', '.join(item['pros'][:2])}")
        print(f"  {RED}Desvantagens:{RESET} {', '.join(item['cons'][:2])}")

    print(f"\n{BOLD}{CYAN}========================================================================================{RESET}")
    print(f"{BOLD}{GREEN}🚀 PRÉVIA TECNOLÓGICA: NVIDIA DLSS 5 (LANÇAMENTO NOVEMBRO / 2026){RESET}")
    print(f"{CYAN}   Filtro Neural de IA sobre Texturas & Fotorrealismo em Tempo Real{RESET}")
    print(f"{CYAN}========================================================================================{RESET}")
    dlss5 = rec.get('dlss5_analysis', {})
    if dlss5:
        print(f"O DLSS 5 introduz a reconstrução neural de texturas através de redes neurais profundas")
        print(f"rodando nos Tensor Cores de 5ª geração, injetando microdetalhes fotográficos nos materiais.\n")
        for h in dlss5.get('hardware_impact', []):
            color = GREEN if '5070 (' in h['model'] else CYAN
            print(f"{BOLD}{color}• {h['model']}{RESET}")
            print(f"  Status: {BOLD}{h['badge']}{RESET} | {YELLOW}{h['vram_usage']}{RESET}")
            print(f"  {h['summary']}\n")

    print(f"{BOLD}{CYAN}========================================================================================{RESET}")
    print(f"💡 Para abrir a interface web com simulador de 15x, análise DLSS 5 e gráficos interativos:")
    print(f"   Execute: {BOLD}python server.py{RESET} ou de 2 cliques em {BOLD}iniciar.bat{RESET}")
    print(f"{BOLD}{CYAN}========================================================================================{RESET}\n")

if __name__ == '__main__':
    main()


