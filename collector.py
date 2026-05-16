import requests
import psycopg2
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ── Configuration ──────────────────────────────────────────
COINGECKO_URL = "https://api.coingecko.com/api/v3"

CRYPTOS = {
    "bitcoin":  "BTC",
    "ethereum": "ETH",
    "binancecoin": "BNB",
    "solana":   "SOL"
}

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", 5432),
        dbname=os.getenv("DB_NAME", "cryptocompare"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "")
    )
    
# ── Récupérer les prix actuels ──────────────────────────────
def fetch_current_prices():
    ids = ",".join(CRYPTOS.keys())
    url = f"{COINGECKO_URL}/simple/price"
    params = {
        "ids": ids,
        "vs_currencies": "usd",
        "include_market_cap": "true",
        "include_24hr_vol": "true",
        "include_24hr_change": "true"
    }

    print("📡 Récupération des prix depuis CoinGecko...")
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()

# ── Récupérer l'historique sur 90 jours ────────────────────
def fetch_historical_prices(crypto_id, days=90):
    url = f"{COINGECKO_URL}/coins/{crypto_id}/market_chart"
    params = {
        "vs_currency": "usd",
        "days": days,
        "interval": "daily"
    }

    print(f"📡 Récupération historique {crypto_id} ({days} jours)...")
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()

# ── Sauvegarder en base ─────────────────────────────────────
def save_prices(data):
    conn = get_db_connection()
    cursor = conn.cursor()

    inserted = 0
    for crypto_id, symbol in CRYPTOS.items():
        if crypto_id not in data:
            continue

        prices = data[crypto_id]
        cursor.execute("""
            INSERT INTO crypto_prices
                (symbol, name, price_usd, market_cap, volume_24h, change_24h)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            symbol,
            crypto_id,
            prices.get("usd", 0),
            prices.get("usd_market_cap", 0),
            prices.get("usd_24h_vol", 0),
            prices.get("usd_24h_change", 0)
        ))
        inserted += 1

    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ {inserted} cryptos sauvegardées en base")

# ── Sauvegarder l'historique ────────────────────────────────
def save_historical(crypto_id, symbol, data):
    conn = get_db_connection()
    cursor = conn.cursor()

    prices = data.get("prices", [])
    volumes = {v[0]: v[1] for v in data.get("total_volumes", [])}

    inserted = 0
    for timestamp_ms, price in prices:
        recorded_at = datetime.fromtimestamp(timestamp_ms / 1000)
        volume = volumes.get(timestamp_ms, 0)

        cursor.execute("""
            INSERT INTO crypto_prices
                (symbol, name, price_usd, volume_24h, recorded_at)
            VALUES (%s, %s, %s, %s, %s)
        """, (symbol, crypto_id, price, volume, recorded_at))
        inserted += 1

    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ {inserted} points historiques sauvegardés pour {symbol}")

# ── Rafraîchir la vue matérialisée ─────────────────────────
def refresh_materialized_view():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("REFRESH MATERIALIZED VIEW mv_daily_prices;")
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Vue matérialisée rafraîchie")

# ── Collecter tout ──────────────────────────────────────────
def collect_all(historical=False):
    if historical:
        print("\n🔄 Collecte de l'historique 90 jours...")
        for crypto_id, symbol in CRYPTOS.items():
            data = fetch_historical_prices(crypto_id, days=90)
            save_historical(crypto_id, symbol, data)
    else:
        data = fetch_current_prices()
        save_prices(data)

    refresh_materialized_view()
    print("\n✅ Collecte terminée")

if __name__ == "__main__":
    collect_all(historical=True)