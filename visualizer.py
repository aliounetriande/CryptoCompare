import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Mode sans interface graphique
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

COLORS = {
    'BTC': '#F7931A',
    'ETH': '#627EEA',
    'BNB': '#F3BA2F',
    'SOL': '#9945FF'
}

def get_engine():
    return create_engine(
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}"
        f"/{os.getenv('DB_NAME')}"
    )

def run_query(sql):
    engine = get_engine()
    df = pd.read_sql_query(sql, engine)
    engine.dispose()
    return df

# ── 1. Évolution des prix normalisés ───────────────────────
def plot_normalized_prices():
    """
    Prix normalisés à 100 au départ pour comparer les performances.
    Si BTC commence à 100 et finit à 112, il a gagné 12%.
    """
    sql = """
        SELECT symbol, jour, prix_moyen
        FROM mv_daily_prices
        ORDER BY symbol, jour
    """
    df = run_query(sql)

    fig, ax = plt.subplots(figsize=(12, 6))

    for symbol in ['BTC', 'ETH', 'BNB', 'SOL']:
        data = df[df['symbol'] == symbol].copy()
        data = data.sort_values('jour')

        # Normaliser à 100 au départ
        data['normalized'] = data['prix_moyen'] / data['prix_moyen'].iloc[0] * 100

        ax.plot(
            data['jour'],
            data['normalized'],
            label=symbol,
            color=COLORS[symbol],
            linewidth=2
        )

    ax.axhline(y=100, color='gray', linestyle='--', alpha=0.5, label='Base 100')
    ax.set_title('Performance comparée — Base 100 (90 jours)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Date')
    ax.set_ylabel('Performance (base 100)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    plt.xticks(rotation=45)

    plt.tight_layout()
    path = f"{REPORTS_DIR}/01_performance_normalisee.png"
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"✅ Graphique sauvegardé : {path}")

# ── 2. Heatmap des corrélations ─────────────────────────────
def plot_correlation_heatmap():
    """
    Matrice de corrélation — chaque case montre comment
    deux cryptos évoluent ensemble.
    """
    sql = """
        SELECT symbol, jour, prix_moyen
        FROM mv_daily_prices
        ORDER BY jour, symbol
    """
    df = run_query(sql)

    # Pivoter : chaque colonne = une crypto, chaque ligne = un jour
    pivot = df.pivot(index='jour', columns='symbol', values='prix_moyen')
    corr_matrix = pivot.corr()

    fig, ax = plt.subplots(figsize=(8, 6))

    symbols = corr_matrix.columns.tolist()
    data = corr_matrix.values

    im = ax.imshow(data, cmap='RdYlGn', vmin=-1, vmax=1)
    plt.colorbar(im, ax=ax, label='Corrélation de Pearson')

    ax.set_xticks(range(len(symbols)))
    ax.set_yticks(range(len(symbols)))
    ax.set_xticklabels(symbols, fontweight='bold')
    ax.set_yticklabels(symbols, fontweight='bold')

    for i in range(len(symbols)):
        for j in range(len(symbols)):
            ax.text(j, i, f'{data[i, j]:.2f}',
                   ha='center', va='center',
                   fontweight='bold', fontsize=12,
                   color='black')

    ax.set_title('Matrice de corrélation des cryptos', fontsize=14, fontweight='bold')
    plt.tight_layout()
    path = f"{REPORTS_DIR}/02_correlation_heatmap.png"
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"✅ Graphique sauvegardé : {path}")

# ── 3. Volatilité ───────────────────────────────────────────
def plot_volatility():
    """
    Volatilité = écart-type des variations de prix journalières.
    Plus c'est élevé, plus la crypto est risquée.
    """
    sql = """
        SELECT symbol, jour, prix_moyen
        FROM mv_daily_prices
        ORDER BY symbol, jour
    """
    df = run_query(sql)

    fig, ax = plt.subplots(figsize=(10, 6))

    for symbol in ['BTC', 'ETH', 'BNB', 'SOL']:
        data = df[df['symbol'] == symbol].copy()
        data = data.sort_values('jour')

        # Calculer les variations journalières en %
        data['variation'] = data['prix_moyen'].pct_change() * 100

        ax.plot(
            data['jour'],
            data['variation'],
            label=f"{symbol} (σ={data['variation'].std():.2f}%)",
            color=COLORS[symbol],
            alpha=0.7,
            linewidth=1.5
        )

    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax.set_title('Variations journalières (%) — Volatilité', fontsize=14, fontweight='bold')
    ax.set_xlabel('Date')
    ax.set_ylabel('Variation (%)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    plt.xticks(rotation=45)

    plt.tight_layout()
    path = f"{REPORTS_DIR}/03_volatilite.png"
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"✅ Graphique sauvegardé : {path}")

# ── 4. Volume de trading ────────────────────────────────────
def plot_volume():
    sql = """
        SELECT symbol, jour, volume_moyen
        FROM mv_daily_prices
        ORDER BY symbol, jour
    """
    df = run_query(sql)

    fig, ax = plt.subplots(figsize=(12, 5))

    bottom = None
    for symbol in ['BTC', 'ETH', 'BNB', 'SOL']:
        data = df[df['symbol'] == symbol].sort_values('jour')
        volumes = data['volume_moyen'].values / 1e9  # En milliards

        if bottom is None:
            ax.bar(data['jour'], volumes,
                  label=symbol, color=COLORS[symbol], alpha=0.8)
            bottom = volumes
        else:
            ax.bar(data['jour'], volumes,
                  bottom=bottom, label=symbol,
                  color=COLORS[symbol], alpha=0.8)
            bottom = bottom + volumes

    ax.set_title('Volume de trading journalier (milliards USD)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Date')
    ax.set_ylabel('Volume (Md USD)')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    plt.xticks(rotation=45)

    plt.tight_layout()
    path = f"{REPORTS_DIR}/04_volume.png"
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"✅ Graphique sauvegardé : {path}")

# ── Main ────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🎨 Génération des graphiques...")
    print("─" * 40)

    try:
        plot_normalized_prices()
    except Exception as e:
        print(f"❌ {e}")

    try:
        plot_correlation_heatmap()
    except Exception as e:
        print(f"❌ {e}")

    try:
        plot_volatility()
    except Exception as e:
        print(f"❌ {e}")

    try:
        plot_volume()
    except Exception as e:
        print(f"❌ {e}")

    print("\n✅ Tous les graphiques sont dans le dossier reports/")