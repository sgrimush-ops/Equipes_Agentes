"""
Módulo de Banco de Dados e Histórico Diário de Preços (RTX 5070 e RTX 5070 Ti)
Utiliza SQLite para persistência diária, cálculo de oscilação (24h, 7d, 30d) e geração de séries temporais.
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
            price_cash REAL NOT NULL,
            price_card REAL NOT NULL,
            url TEXT,
            is_limited_promo INTEGER DEFAULT 0,
            promo_badge TEXT,
            in_stock INTEGER DEFAULT 1
        )
    ''')
    
    # Adicionar colunas se tabela ja existia
    try:
        cursor.execute("ALTER TABLE daily_snapshots ADD COLUMN cooling_type TEXT")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE daily_snapshots ADD COLUMN is_limited_promo INTEGER DEFAULT 0")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE daily_snapshots ADD COLUMN promo_badge TEXT")
    except Exception:
        pass
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_aggregates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            gpu_model TEXT NOT NULL,
            store_key TEXT NOT NULL,
            min_price_cash REAL NOT NULL,
            avg_price_cash REAL NOT NULL,
            max_price_cash REAL NOT NULL,
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
    
    # Limpa eventuais dados antigos da 5080
    cursor.execute("DELETE FROM daily_snapshots WHERE gpu_model = 'RTX 5080'")
    cursor.execute("DELETE FROM daily_aggregates WHERE gpu_model = 'RTX 5080'")

    conn.commit()
    conn.close()

def save_daily_snapshot(offers: List[Dict[str, Any]], target_date: Optional[str] = None) -> int:
    """Grava as ofertas do dia atual no histórico."""
    if not offers:
        return 0

    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    
    now = datetime.now()
    date_str = target_date or now.strftime('%Y-%m-%d')
    timestamp_str = now.isoformat()

    cursor.execute('DELETE FROM daily_snapshots WHERE date = ?', (date_str,))

    # Filtra apenas 5070 e 5070 Ti
    valid_offers = [o for o in offers if o.get('gpu_model') in ['RTX 5070', 'RTX 5070 Ti']]

    for o in valid_offers:
        cursor.execute('''
            INSERT INTO daily_snapshots (
                date, timestamp, store, store_key, gpu_model, brand, title, cooling_type, price_cash, price_card, url, is_limited_promo, promo_badge, in_stock
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            date_str,
            timestamp_str,
            o.get('store', ''),
            o.get('store_key', ''),
            o.get('gpu_model', ''),
            o.get('brand', ''),
            o.get('title', ''),
            o.get('cooling_type', 'Dual / Triplo Fan'),
            float(o.get('price_cash', 0)),
            float(o.get('price_card', 0)),
            o.get('url', ''),
            1 if o.get('is_limited_promo') else 0,
            o.get('promo_badge', ''),
            1 if o.get('in_stock', True) else 0
        ))

    cursor.execute('DELETE FROM daily_aggregates WHERE date = ?', (date_str,))
    
    stores = ['kabum', 'pichau', 'terabyte', 'all']
    models = ['RTX 5070', 'RTX 5070 Ti']

    for m in models:
        for sk in stores:
            if sk == 'all':
                subset = [o for o in valid_offers if o.get('gpu_model') == m and float(o.get('price_cash', 0)) > 0]
            else:
                subset = [o for o in valid_offers if o.get('gpu_model') == m and o.get('store_key') == sk and float(o.get('price_cash', 0)) > 0]
            
            if subset:
                prices = [float(x.get('price_cash', 0)) for x in subset]
                best = min(subset, key=lambda x: float(x.get('price_cash', 0)))
                cursor.execute('''
                    INSERT OR REPLACE INTO daily_aggregates (
                        date, gpu_model, store_key, min_price_cash, avg_price_cash, max_price_cash, best_offer_title, best_offer_url, offers_count
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    date_str,
                    m,
                    sk,
                    min(prices),
                    round(sum(prices) / len(prices), 2),
                    max(prices),
                    best.get('title', ''),
                    best.get('url', ''),
                    len(subset)
                ))

    conn.commit()
    conn.close()
    print(f"[History DB] Snapshot do dia {date_str} salvo com sucesso ({len(valid_offers)} ofertas).")
    return len(valid_offers)

def get_daily_timeline(days: int = 30, gpu_model: Optional[str] = None, store_key: str = 'all') -> Dict[str, Any]:
    """Retorna os pontos da série temporal para plotagem nos gráficos de oscilação."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    models = [gpu_model] if gpu_model and gpu_model != 'ALL' and gpu_model in ['RTX 5070', 'RTX 5070 Ti'] else ['RTX 5070', 'RTX 5070 Ti']
    
    timeline_data = {
        'dates': [],
        'series': {}
    }

    cursor.execute('''
        SELECT DISTINCT date FROM daily_aggregates 
        WHERE date >= ? AND gpu_model IN ('RTX 5070', 'RTX 5070 Ti')
        ORDER BY date ASC
    ''', (start_date,))
    dates = [row['date'] for row in cursor.fetchall()]
    timeline_data['dates'] = dates

    for m in models:
        timeline_data['series'][m] = {
            'min_prices': [],
            'avg_prices': [],
            'best_stores': []
        }
        for d in dates:
            cursor.execute('''
                SELECT min_price_cash, avg_price_cash, best_offer_title, best_offer_url 
                FROM daily_aggregates 
                WHERE date = ? AND gpu_model = ? AND store_key = ?
            ''', (d, m, store_key))
            row = cursor.fetchone()
            if row:
                timeline_data['series'][m]['min_prices'].append(row['min_price_cash'])
                timeline_data['series'][m]['avg_prices'].append(row['avg_price_cash'])
            else:
                timeline_data['series'][m]['min_prices'].append(None)
                timeline_data['series'][m]['avg_prices'].append(None)

    conn.close()
    return timeline_data

def get_price_variation_stats() -> Dict[str, Any]:
    """Calcula a variação de preços de 24 horas, 7 dias e recorde histórico para 5070 e 5070 Ti."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    models = ['RTX 5070', 'RTX 5070 Ti']
    today_str = datetime.now().strftime('%Y-%m-%d')
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    seven_days_ago_str = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

    stats_result = {}

    for m in models:
        cursor.execute('''
            SELECT min_price_cash, avg_price_cash, best_offer_title, best_offer_url
            FROM daily_aggregates WHERE date = ? AND gpu_model = ? AND store_key = 'all'
        ''', (today_str, m))
        current_row = cursor.fetchone()

        if not current_row:
            cursor.execute('''
                SELECT min_price_cash, avg_price_cash, best_offer_title, best_offer_url, date
                FROM daily_aggregates WHERE gpu_model = ? AND store_key = 'all'
                ORDER BY date DESC LIMIT 1
            ''', (m,))
            current_row = cursor.fetchone()

        current_price = current_row['min_price_cash'] if current_row else 0.0

        cursor.execute('''
            SELECT min_price_cash FROM daily_aggregates 
            WHERE date <= ? AND gpu_model = ? AND store_key = 'all'
            ORDER BY date DESC LIMIT 1
        ''', (yesterday_str, m))
        yesterday_row = cursor.fetchone()
        yesterday_price = yesterday_row['min_price_cash'] if yesterday_row else current_price

        cursor.execute('''
            SELECT min_price_cash FROM daily_aggregates 
            WHERE date <= ? AND gpu_model = ? AND store_key = 'all'
            ORDER BY date DESC LIMIT 1
        ''', (seven_days_ago_str, m))
        seven_days_row = cursor.fetchone()
        seven_days_price = seven_days_row['min_price_cash'] if seven_days_row else current_price

        cursor.execute('''
            SELECT min_price_cash, date, best_offer_title FROM daily_aggregates 
            WHERE gpu_model = ? AND store_key = 'all'
            ORDER BY min_price_cash ASC LIMIT 1
        ''', (m,))
        min_historical_row = cursor.fetchone()

        cursor.execute('''
            SELECT max_price_cash, date FROM daily_aggregates 
            WHERE gpu_model = ? AND store_key = 'all'
            ORDER BY max_price_cash DESC LIMIT 1
        ''', (m,))
        max_historical_row = cursor.fetchone()

        diff_24h = current_price - yesterday_price
        pct_24h = ((diff_24h) / yesterday_price * 100) if yesterday_price > 0 else 0.0

        diff_7d = current_price - seven_days_price
        pct_7d = ((diff_7d) / seven_days_price * 100) if seven_days_price > 0 else 0.0

        trend = 'stable'
        if pct_24h < -0.5:
            trend = 'falling'
        elif pct_24h > 0.5:
            trend = 'rising'

        stats_result[m] = {
            'current_min_price': current_price,
            'yesterday_price': yesterday_price,
            'diff_24h': round(diff_24h, 2),
            'pct_24h': round(pct_24h, 2),
            'diff_7d': round(diff_7d, 2),
            'pct_7d': round(pct_7d, 2),
            'trend': trend,
            'all_time_low': min_historical_row['min_price_cash'] if min_historical_row else current_price,
            'all_time_low_date': min_historical_row['date'] if min_historical_row else today_str,
            'all_time_high': max_historical_row['max_price_cash'] if max_historical_row else current_price,
            'is_at_all_time_low': current_price <= (min_historical_row['min_price_cash'] if min_historical_row else current_price)
        }

    conn.close()
    return stats_result

def seed_sample_history_if_needed():
    """Popula histórico retroativo realista para RTX 5070 e RTX 5070 Ti."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM daily_aggregates WHERE gpu_model IN ('RTX 5070', 'RTX 5070 Ti')")
    count = cursor.fetchone()['count']
    conn.close()

    if count >= 10:
        return

    base_prices = {
        'RTX 5070': [
            5499.99, 5499.99, 5399.90, 5399.90, 5299.99, 5299.99, 5199.90,
            5199.90, 5249.00, 5249.00, 5149.99, 5099.90, 4999.99, 4999.99,
            5099.00, 5099.00, 4999.99, 4949.00, 4949.00, 4899.99, 4899.99,
            4999.00, 4999.00, 4920.00, 4899.99, 4899.99, 4950.00, 4899.99, 4899.99, 4899.99
        ],
        'RTX 5070 Ti': [
            9199.00, 9199.00, 8999.99, 8999.99, 8899.00, 8799.90, 8699.99,
            8699.99, 8749.00, 8699.00, 8599.90, 8499.00, 8399.99, 8399.99,
            8499.00, 8499.00, 8399.99, 8299.00, 8299.00, 8199.99, 8199.99,
            8299.00, 8299.00, 8249.00, 8199.99, 8199.99, 8250.00, 8199.99, 8199.99, 8199.99
        ]
    }

    now = datetime.now()
    conn = get_connection()
    cursor = conn.cursor()

    for i in range(29, -1, -1):
        day_date = (now - timedelta(days=i)).strftime('%Y-%m-%d')
        idx = 29 - i
        for m, prices in base_prices.items():
            price = prices[idx]
            cursor.execute('''
                INSERT OR REPLACE INTO daily_aggregates (
                    date, gpu_model, store_key, min_price_cash, avg_price_cash, max_price_cash, best_offer_title, best_offer_url, offers_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                day_date,
                m,
                'all',
                price,
                round(price * 1.08, 2),
                round(price * 1.25, 2),
                f"Oferta {m} em {day_date}",
                "https://www.pichau.com.br",
                3
            ))

    conn.commit()
    conn.close()

seed_sample_history_if_needed()
