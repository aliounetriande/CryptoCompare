import sys
from collector import collect_all
from analyzer import (
    performance_90_days,
    volatility_analysis,
    correlation_analysis,
    detect_decoupling
)
from visualizer import (
    plot_normalized_prices,
    plot_correlation_heatmap,
    plot_volatility,
    plot_volume
)

def main():
    print("=" * 55)
    print("   CryptoCompare — Crypto Correlation Analyzer")
    print("=" * 55)

    mode = sys.argv[1] if len(sys.argv) > 1 else "all"

    if mode in ("collect", "all"):
        print("\n🔄 Étape 1 — Collecte des données...")
        collect_all(historical=False)

    if mode in ("analyze", "all"):
        print("\n📊 Étape 2 — Analyse...")
        performance_90_days()
        volatility_analysis()
        correlation_analysis()
        detect_decoupling()

    if mode in ("visualize", "all"):
        print("\n🎨 Étape 3 — Génération des graphiques...")
        plot_normalized_prices()
        plot_correlation_heatmap()
        plot_volatility()
        plot_volume()

    print("\n✅ CryptoCompare terminé")
    print("📁 Graphiques disponibles dans : reports/")

if __name__ == "__main__":
    main()