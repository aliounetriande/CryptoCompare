import psycopg2
import pandas as pd
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

def get_engine():
    return create_engine(
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}"
        f"/{os.getenv('DB_NAME')}"
    )

def run_query(sql, params=None):
    engine = get_engine()
    df = pd.read_sql_query(sql, engine, params=params)
    engine.dispose()
    return df

# ── 1. Performance globale sur 90 jours ────────────────────
def performance_90_days():
    print("\n📊 Performance sur 90 jours")
    print("─" * 50)

    sql = """
        SELECT
            symbol,
            FIRST_VALUE(prix_moyen) OVER (
                PARTITION BY symbol ORDER BY jour ASC
            )::decimal(20,2)                        AS prix_debut,
            LAST_VALUE(prix_moyen) OVER (
                PARTITION BY symbol
                ORDER BY jour ASC
                ROWS BETWEEN UNBOUNDED PRECEDING
                         AND UNBOUNDED FOLLOWING
            )::decimal(20,2)                        AS prix_fin,
            ROUND(
                (LAST_VALUE(prix_moyen) OVER (
                    PARTITION BY symbol
                    ORDER BY jour ASC
                    ROWS BETWEEN UNBOUNDED PRECEDING
                             AND UNBOUNDED FOLLOWING
                ) - FIRST_VALUE(prix_moyen) OVER (
                    PARTITION BY symbol ORDER BY jour ASC
                )) * 100.0 / FIRST_VALUE(prix_moyen) OVER (
                    PARTITION BY symbol ORDER BY jour ASC
                ), 2
            )                                       AS variation_pct
        FROM mv_daily_prices
        GROUP BY symbol, jour, prix_moyen
        ORDER BY variation_pct DESC
    """

    df = run_query(sql)
    df_unique = df.drop_duplicates(subset=['symbol'])
    print(df_unique[['symbol', 'prix_debut', 'prix_fin', 'variation_pct']].to_string(index=False))
    return df_unique

# ── 2. Volatilité par crypto ────────────────────────────────
def volatility_analysis():
    print("\n📈 Volatilité sur 90 jours (écart-type des variations)")
    print("─" * 50)

    sql = """
        SELECT
            symbol,
            ROUND(AVG(variation_moyenne)::numeric, 4)   AS variation_moy,
            ROUND(STDDEV(variation_moyenne)::numeric, 4) AS volatilite,
            ROUND(MAX(prix_max)::numeric, 2)             AS prix_max,
            ROUND(MIN(prix_min)::numeric, 2)             AS prix_min,
            ROUND((MAX(prix_max) - MIN(prix_min)) * 100.0
                  / MIN(prix_min), 2)                   AS amplitude_pct
        FROM mv_daily_prices
        GROUP BY symbol
        ORDER BY volatilite DESC
    """

    df = run_query(sql)
    print(df.to_string(index=False))
    return df

# ── 3. Corrélation entre cryptos ───────────────────────────
def correlation_analysis():
    print("\n🔗 Corrélation entre cryptos (Pearson)")
    print("─" * 50)
    print("Rappel : +1 = évoluent ensemble, 0 = aucun lien, -1 = sens inverse")
    print()

    cryptos = ['BTC', 'ETH', 'BNB', 'SOL']
    results = []

    conn = get_engine().raw_connection()
    cursor = conn.cursor()

    for i in range(len(cryptos)):
        for j in range(i + 1, len(cryptos)):
            crypto_a = cryptos[i]
            crypto_b = cryptos[j]

            cursor.execute("""
                SELECT ROUND(corr(a.prix_moyen, b.prix_moyen)::numeric, 4)
                FROM mv_daily_prices a
                JOIN mv_daily_prices b
                    ON a.jour = b.jour
                WHERE a.symbol = %s
                  AND b.symbol = %s
            """, (crypto_a, crypto_b))

            correlation = cursor.fetchone()[0]
            results.append({
                'Paire': f"{crypto_a} / {crypto_b}",
                'Corrélation': correlation,
                'Interprétation': interpret_correlation(float(correlation))
            })

    cursor.close()
    conn.close()

    df = pd.DataFrame(results)
    print(df.to_string(index=False))
    return df

def interpret_correlation(value):
    if value >= 0.9:
        return "🔴 Très forte"
    elif value >= 0.7:
        return "🟠 Forte"
    elif value >= 0.5:
        return "🟡 Modérée"
    elif value >= 0.3:
        return "🟢 Faible"
    else:
        return "⚪ Très faible"

# ── 4. Jours de découplage ──────────────────────────────────
def detect_decoupling():
    print("\n🔍 Jours de découplage BTC/ETH")
    print("─" * 50)
    print("(jours où BTC et ETH évoluent en sens contraire)")
    print()

    sql = """
        SELECT
            a.jour,
            ROUND(a.variation_moyenne::numeric, 2) AS variation_btc,
            ROUND(b.variation_moyenne::numeric, 2) AS variation_eth,
            ROUND((a.variation_moyenne - b.variation_moyenne)::numeric, 2) AS ecart
        FROM mv_daily_prices a
        JOIN mv_daily_prices b ON a.jour = b.jour
        WHERE a.symbol = 'BTC'
          AND b.symbol = 'ETH'
          AND SIGN(a.variation_moyenne) != SIGN(b.variation_moyenne)
        ORDER BY ABS(a.variation_moyenne - b.variation_moyenne) DESC
        LIMIT 10
    """

    df = run_query(sql)
    if df.empty:
        print("Aucun découplage significatif détecté.")
    else:
        print(df.to_string(index=False))
    return df

# ── Main ────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("   CryptoCompare — Analyse des corrélations")
    print("=" * 50)

    performance_90_days()
    volatility_analysis()
    correlation_analysis()
    detect_decoupling()

    print("\n✅ Analyse terminée")