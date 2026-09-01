"""
Servidor Web e API REST para a Ferramenta de Cotação de GPUs RTX 5000 (RTX 5070 e RTX 5070 Ti)
Inclui Histórico Diário de Preços, Monitor de Oscilação e Banco SQLite.
"""

import sys
import os

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import http.server
import socketserver
import json
import urllib.parse
import threading
import webbrowser
from typing import Dict, Any

from scraper_engine import collect_all_offers
from cost_benefit_engine import enrich_and_score_offers
from history_db import save_daily_snapshot, get_daily_timeline, get_price_variation_stats, seed_sample_history_if_needed

PORT = 5000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

CACHE_DATA: Dict[str, Any] = {}
IS_UPDATING = False

def update_cache(live: bool = True):
    global CACHE_DATA, IS_UPDATING
    IS_UPDATING = True
    try:
        print(f"[Server] Atualizando dados (live={live})...")
        offers = collect_all_offers(live_scrape=live)
        result = enrich_and_score_offers(offers)
        
        if offers:
            save_daily_snapshot(offers)
            
        result['variation_stats'] = get_price_variation_stats()
        
        CACHE_DATA = result
        print(f"[Server] Cache atualizado com sucesso! {len(offers)} ofertas.")
    except Exception as e:
        print(f"[Server Error] Falha ao atualizar cache: {e}")
    finally:
        IS_UPDATING = False

seed_sample_history_if_needed()
update_cache(live=False)

class GPUHunterRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        if path == '/api/gpus':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                'status': 'success',
                'is_updating': IS_UPDATING,
                'data': CACHE_DATA
            }
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            return

        elif path == '/api/history':
            days = int(query.get('days', ['30'])[0])
            model = query.get('model', ['ALL'])[0]
            store = query.get('store', ['all'])[0]
            
            timeline = get_daily_timeline(days=days, gpu_model=model if model != 'ALL' else None, store_key=store)
            variations = get_price_variation_stats()

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                'status': 'success',
                'days': days,
                'model': model,
                'store': store,
                'timeline': timeline,
                'variations': variations
            }
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            return

        elif path == '/api/history/variation':
            variations = get_price_variation_stats()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'success', 'data': variations}, ensure_ascii=False).encode('utf-8'))
            return

        elif path == '/api/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'is_updating': IS_UPDATING}, ensure_ascii=False).encode('utf-8'))
            return

        elif path == '/api/export/csv':
            self.send_response(200)
            self.send_header('Content-Type', 'text/csv; charset=utf-8')
            self.send_header('Content-Disposition', 'attachment; filename="cotacao_rtx5070_5070ti.csv"')
            self.end_headers()
            
            csv_lines = ["Loja;Modelo GPU;Fabricante;Titulo;Preco A Vista PIX (R$);Preco Cartao 10x/12x (R$);Prestacao 15x (+10% acrescimo) (R$);Total 15x (R$);Custo por FPS 1440p (R$);Custo por FPS 4K Nativo (R$);Score Custo-Beneficio;Link"]
            for o in CACHE_DATA.get('offers', []):
                line = f"{o['store']};{o['gpu_model']};{o['brand']};\"{o['title']}\";{o['price_cash']};{o['price_card']};{o.get('installment_15x_val', 0)};{o.get('price_15x_total', 0)};{o.get('cost_per_fps_1440p', 0)};{o.get('cost_per_fps_4k', 0)};{o.get('cost_benefit_score', 0)};{o['url']}"
                csv_lines.append(line)
            
            self.wfile.write("\n".join(csv_lines).encode('utf-8-sig'))
            return


        elif path == '/api/history/export/csv':
            self.send_response(200)
            self.send_header('Content-Type', 'text/csv; charset=utf-8')
            self.send_header('Content-Disposition', 'attachment; filename="historico_diario_rtx5070_5070ti.csv"')
            self.end_headers()
            
            from history_db import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT date, gpu_model, store_key, min_price_cash, avg_price_cash, max_price_cash, best_offer_title FROM daily_aggregates WHERE gpu_model IN ('RTX 5070', 'RTX 5070 Ti') ORDER BY date DESC, gpu_model ASC")
            rows = cursor.fetchall()
            conn.close()

            csv_lines = ["Data;Modelo GPU;Filtro Loja;Menor Preco (R$);Preco Medio (R$);Maior Preco (R$);Melhor Oferta Registrada"]
            for r in rows:
                csv_lines.append(f"{r['date']};{r['gpu_model']};{r['store_key']};{r['min_price_cash']};{r['avg_price_cash']};{r['max_price_cash']};\"{r['best_offer_title']}\"")

            self.wfile.write("\n".join(csv_lines).encode('utf-8-sig'))
            return

        return super().do_GET()

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path == '/api/refresh':
            global IS_UPDATING
            if not IS_UPDATING:
                t = threading.Thread(target=update_cache, kwargs={'live': True})
                t.daemon = True
                t.start()
                status_msg = "Varredura iniciada para RTX 5070 e RTX 5070 Ti."
            else:
                status_msg = "Varredura já está em andamento."

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok', 'message': status_msg}, ensure_ascii=False).encode('utf-8'))
            return

        self.send_error(404, "Endpoint não encontrado")

def run_server(open_browser: bool = True):
    global PORT
    
    httpd = None
    for p in range(5000, 5030):
        try:
            httpd = socketserver.TCPServer(('', p), GPUHunterRequestHandler)
            PORT = p
            break
        except OSError:
            continue
            
    if httpd is None:
        print("[Erro] Não foi possível vincular a nenhuma porta.")
        return

    url = f"http://127.0.0.1:{PORT}"
    print(f"\n========================================================")
    print(f" [*] GPU Hunter & Cost-Benefit Analyzer Pro iniciado!")
    print(f" [>] Acesse no seu navegador: {url}")
    print(f" [*] Monitorando: KaBuM!, Pichau e TerabyteShop")
    print(f" [*] Placas: RTX 5070 e RTX 5070 Ti")
    print(f"========================================================\n")

    if open_browser:
        print(f" [*] Abrindo navegador automaticamente em {url} ...")
        threading.Timer(0.8, lambda: webbrowser.open(url, new=2)).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado pelo usuário.")
        httpd.server_close()

if __name__ == '__main__':
    open_browser_flag = '--no-browser' not in sys.argv
    run_server(open_browser=open_browser_flag)

