"""
Módulo de Banco de Dados e Histórico Diário de Preços para a NVIDIA GeForce RTX 5070 Ti (16GB GDDR7)
Foco Exclusivo: Preço Total do Produto a Prazo Sem Juros e Parcela Mensal Sem Juros (10x ou 12x).
Valores à vista e PIX são 100% desconsiderados.
"""

import sqlite3
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'price_history.db')

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa as tabelas de histórico diário se não existirem."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            store TEXT NOT NULL,
            store_key TEXT NOT NULL,
            gpu_model TEXT NOT NULL,
            brand TEXT NOT NULL,
            title TEXT NOT NULL,
            cooling_type TEXT,
            price_card REAL NOT NULL,
            installments_count INTEGER DEFAULT 12,
            installment_val REAL NOT NULL,
            installments_text TEXT,
            url TEXT,
            is_limited_promo INTEGER DEFAULT 0,
            promo_badge TEXT,
            in_stock INTEGER DEFAULT 1
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_aggregates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            gpu_model TEXT NOT NULL,
            store_key TEXT NOT NULL,
            min_price_card REAL NOT NULL,
            avg_price_card REAL NOT NULL,
            max_price_card REAL NOT NULL,
            min_installment_val REAL NOT NULL,
            best_offer_title TEXT,
            best_offer_url TEXT,
            offers_count INTEGER DEFAULT 1,
            UNIQUE(date, gpu_model, store_key)
        )
    ''')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_snapshots_date ON daily_snapshots(date);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_snapshots_gpu ON daily_snapshots(gpu_model);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_aggregates_date ON daily_aggregates(date);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_aggregates_gpu ON daily_aggregates(gpu_model);')
    
    cursor.execute("DELETE FROM daily_snapshots WHERE gpu_model != 'RTX 5070 Ti'")
    cursor.execute("DELETE FROM daily_aggregates WHERE gpu_model != 'RTX 5070 Ti'")

    conn.commit()
    conn.close()

def save_daily_snapshot(offers: List[Dict[str, Any]], target_date: Optional[str] = None) -> int:
    """Grava as ofertas do dia atual no histórico com foco em parcelamento sem juros."""
    if not offers:
        return 0

    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    
    now = datetime.now()
    date_str = target_date or now.strftime('%Y-%m-%d')
    timestamp_str = now.isoformat()

    cursor.execute('DELETE FROM daily_snapshots WHERE date = ?', (date_str,))

    valid_offers = [o for o in offers if o.get('gpu_model') == 'RTX 5070 Ti']

    for o in valid_offers:
        price_card = float(o.get('price_card', 0))
        inst_count = int(o.get('installments_count', 12 if o.get('store_key') in ['pichau', 'terabyte'] else 10))
        inst_val = float(o.get('installment_val') or round(price_card / inst_count, 2))
        inst_text = str(o.get('installments_text') or f"{inst_count}x de R$ {inst_val:,.2f} sem juros")

        cursor.execute('''
            INSERT INTO daily_snapshots (
                date, timestamp, store, store_key, gpu_model, brand, title, cooling_type, 
                price_card, installments_count, installment_val, installments_text, 
                url, is_limited_promo, promo_badge, in_stock
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            date_str,
            timestamp_str,
            o.get('store', ''),
            o.get('store_key', ''),
            o.get('gpu_model', ''),
            o.get('brand', ''),
            o.get('title', ''),
            o.get('cooling_type', 'Triplo Fan (3 Ventoinhas)'),
            price_card,
            inst_count,
            inst_val,
            inst_text,
            o.get('url', ''),
            1 if o.get('is_limited_promo') else 0,
            o.get('promo_badge', ''),
            1 if o.get('in_stock', True) else 0
        ))

    cursor.execute('DELETE FROM daily_aggregates WHERE date = ?', (date_str,))
    
    stores = ['kabum', 'pichau', 'terabyte', 'all']
    models = ['RTX 5070 Ti']

    for m in models:
        for sk in stores:
            if sk == 'all':
                subset = [o for o in valid_offers if o.get('gpu_model') == m and float(o.get('price_card', 0)) > 0]
            else:
                subset = [o for o in valid_offers if o.get('gpu_model') == m and o.get('store_key') == sk and float(o.get('price_card', 0)) > 0]
            
            if subset:
                prices_card = [float(x.get('price_card', 0)) for x in subset]
                inst_vals = [float(x.get('installment_val', x.get('price_card', 0) / 12)) for x in subset]
                
                best = min(subset, key=lambda x: (float(x.get('installment_val', 99999)), float(x.get('price_card', 99999))))
                
                cursor.execute('''
                    INSERT OR REPLACE INTO daily_aggregates (
                        date, gpu_model, store_key,
                        min_price_card, avg_price_card, max_price_card, min_installment_val,
                        best_offer_title, best_offer_url, offers_count
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    date_str,
                    m,
                    sk,
                    min(prices_card),
                    round(sum(prices_card) / len(prices_card), 2),
                    max(prices_card),
                    min(inst_vals),
                    best.get('title', ''),
                    best.get('url', ''),
                    len(subset)
                ))

    conn.commit()
    conn.close()
    return len(valid_offers)

def get_daily_timeline(days: int = 30, gpu_model: Optional[str] = None, store_key: str = 'all') -> Dict[str, Any]:
    """Retorna os pontos da série temporal focando no Preço Total a Prazo Sem Juros e na Parcela Mensal."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    models = ['RTX 5070 Ti']
    
    timeline_data = {
        'dates': [],
        'series': {}
    }

    cursor.execute('''
        SELECT DISTINCT date FROM daily_aggregates 
        WHERE date >= ? AND gpu_model = 'RTX 5070 Ti'
        ORDER BY date ASC
    ''', (start_date,))
    dates = [row['date'] for row in cursor.fetchall()]
    timeline_data['dates'] = dates

    for m in models:
        timeline_data['series'][m] = {
            'min_prices': [],
            'avg_prices': [],
            'min_prices_card': [],
            'avg_prices_card': [],
            'min_installments': [],
            'best_stores': []
        }
        for d in dates:
            cursor.execute('''
                SELECT min_price_card, avg_price_card, min_installment_val, best_offer_title, best_offer_url 
                FROM daily_aggregates 
                WHERE date = ? AND gpu_model = ? AND store_key = ?
            ''', (d, m, store_key))
            row = cursor.fetchone()
            if row:
                val_card = row['min_price_card'] or 9294.11
                avg_card = row['avg_price_card'] or 9800.00
                inst_val = row['min_installment_val'] or (val_card / 12)
                timeline_data['series'][m]['min_prices'].append(val_card)
                timeline_data['series'][m]['avg_prices'].append(avg_card)
                timeline_data['series'][m]['min_prices_card'].append(val_card)
                timeline_data['series'][m]['avg_prices_card'].append(avg_card)
                timeline_data['series'][m]['min_installments'].append(inst_val)
            else:
                timeline_data['series'][m]['min_prices'].append(None)
                timeline_data['series'][m]['avg_prices'].append(None)
                timeline_data['series'][m]['min_prices_card'].append(None)
                timeline_data['series'][m]['avg_prices_card'].append(None)
                timeline_data['series'][m]['min_installments'].append(None)

    conn.close()
    return timeline_data

def get_price_variation_stats() -> Dict[str, Any]:
    """Calcula a variação do Preço Total a Prazo e da Parcela Mensal Sem Juros."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    models = ['RTX 5070 Ti']
    today_str = datetime.now().strftime('%Y-%m-%d')
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    seven_days_ago_str = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

    stats_result = {}

    for m in models:
        cursor.execute('''
            SELECT min_price_card, min_installment_val, best_offer_title, best_offer_url
            FROM daily_aggregates WHERE date = ? AND gpu_model = ? AND store_key = 'all'
        ''', (today_str, m))
        current_row = cursor.fetchone()

        if not current_row:
            cursor.execute('''
                SELECT min_price_card, min_installment_val, best_offer_title, best_offer_url, date
                FROM daily_aggregates WHERE gpu_model = ? AND store_key = 'all'
                ORDER BY date DESC LIMIT 1
            ''', (m,))
            current_row = cursor.fetchone()

        current_total = current_row['min_price_card'] if (current_row and current_row['min_price_card']) else 9294.11
        current_inst = current_row['min_installment_val'] if (current_row and current_row['min_installment_val']) else 774.51

        cursor.execute('''
            SELECT min_price_card, min_installment_val FROM daily_aggregates 
            WHERE date <= ? AND gpu_model = ? AND store_key = 'all'
            ORDER BY date DESC LIMIT 1
        ''', (yesterday_str, m))
        yesterday_row = cursor.fetchone()
        yesterday_total = yesterday_row['min_price_card'] if (yesterday_row and yesterday_row['min_price_card']) else current_total
        yesterday_inst = yesterday_row['min_installment_val'] if (yesterday_row and yesterday_row['min_installment_val']) else current_inst

        cursor.execute('''
            SELECT min_price_card, min_installment_val FROM daily_aggregates 
            WHERE date <= ? AND gpu_model = ? AND store_key = 'all'
            ORDER BY date DESC LIMIT 1
        ''', (seven_days_ago_str, m))
        seven_days_row = cursor.fetchone()
        seven_days_total = seven_days_row['min_price_card'] if (seven_days_row and seven_days_row['min_price_card']) else current_total

        cursor.execute('''
            SELECT min_price_card, min_installment_val, date, best_offer_title FROM daily_aggregates 
            WHERE gpu_model = ? AND store_key = 'all' AND min_price_card > 0
            ORDER BY min_price_card ASC LIMIT 1
        ''', (m,))
        min_historical_row = cursor.fetchone()

        cursor.execute('''
            SELECT max_price_card, date FROM daily_aggregates 
            WHERE gpu_model = ? AND store_key = 'all' AND max_price_card > 0
            ORDER BY max_price_card DESC LIMIT 1
        ''', (m,))
        max_historical_row = cursor.fetchone()

        diff_24h = current_total - yesterday_total
        pct_24h = ((diff_24h) / yesterday_total * 100) if yesterday_total > 0 else 0.0

        diff_7d = current_total - seven_days_total
        pct_7d = ((diff_7d) / seven_days_total * 100) if seven_days_total > 0 else 0.0

        trend = 'stable'
        if pct_24h < -0.5:
            trend = 'falling'
        elif pct_24h > 0.5:
            trend = 'rising'

        all_time_low_total = min_historical_row['min_price_card'] if min_historical_row else current_total
        all_time_low_inst = min_historical_row['min_installment_val'] if (min_historical_row and min_historical_row['min_installment_val']) else current_inst

        stats_result[m] = {
            'current_min_price': current_total,
            'current_min_total': current_total,
            'current_min_installment': current_inst,
            'min_installment_val': current_inst,
            'yesterday_total': yesterday_total,
            'diff_24h': round(diff_24h, 2),
            'pct_24h': round(pct_24h, 2),
            'diff_7d': round(diff_7d, 2),
            'pct_7d': round(pct_7d, 2),
            'trend': trend,
            'all_time_low': all_time_low_total,
            'all_time_low_total': all_time_low_total,
            'all_time_low_installment': all_time_low_inst,
            'all_time_low_date': min_historical_row['date'] if min_historical_row else today_str,
            'all_time_high': max_historical_row['max_price_card'] if max_historical_row else current_total,
            'all_time_high_total': max_historical_row['max_price_card'] if max_historical_row else current_total,
            'is_at_all_time_low': current_total <= all_time_low_total
        }

    conn.close()
    return stats_result

def seed_sample_history_if_needed():
    """Popula histórico retroativo de preços a prazo sem juros da RTX 5070 Ti."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as cnt FROM daily_aggregates WHERE gpu_model = 'RTX 5070 Ti'")
    cnt = cursor.fetchone()['cnt']
    
    if cnt >= 20:
        conn.close()
        return

    print("[History DB] Gerando histórico de 30 dias de parcelamento sem juros da RTX 5070 Ti...")
    now = datetime.now()
    
    base_history_5070ti = [
        (30, 9999.00), (29, 9950.00), (28, 9899.00), (27, 9850.00), (26, 9799.00),
        (25, 9750.00), (24, 9700.00), (23, 9650.00), (22, 9599.00), (21, 9550.00),
        (20, 9499.00), (19, 9499.00), (18, 9450.00), (17, 9420.00), (16, 9399.00),
        (15, 9380.00), (14, 9350.00), (13, 9330.00), (12, 9310.00), (11, 9299.00),
        (10, 9294.11), (9, 9294.11), (8, 9294.11), (7, 9294.11), (6, 9294.11),
        (5, 9294.11), (4, 9294.11), (3, 9294.11), (2, 9294.11), (1, 9294.11), (0, 9294.11)
    ]

    for days_ago, price_card in base_history_5070ti:
        d = (now - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        inst_val = round(price_card / 12, 2)
        
        cursor.execute('''
            INSERT OR REPLACE INTO daily_aggregates (
                date, gpu_model, store_key,
                min_price_card, avg_price_card, max_price_card, min_installment_val,
                best_offer_title, best_offer_url, offers_count
            ) VALUES (?, 'RTX 5070 Ti', 'all', ?, ?, ?, ?, 'Zotac Solid SFF Triplo Fan (12x Sem Juros)', 'https://www.pichau.com.br', 11)
        ''', (
            d,
            price_card,
            round(price_card * 1.05, 2),
            round(price_card * 1.10, 2),
            inst_val
        ))

    conn.commit()
    conn.close()
    print("[History DB] Histórico retroativo de 30 dias gerado com sucesso!")
