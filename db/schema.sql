-- Table principale des prix crypto
CREATE TABLE IF NOT EXISTS crypto_prices (
    id          BIGSERIAL PRIMARY KEY,
    symbol      VARCHAR(10)     NOT NULL,
    name        VARCHAR(50)     NOT NULL,
    price_usd   DECIMAL(20,8)   NOT NULL,
    market_cap  BIGINT,
    volume_24h  BIGINT,
    change_24h  DECIMAL(10,4),
    recorded_at TIMESTAMP       NOT NULL DEFAULT NOW()
);

-- Index pour accélérer les requêtes par crypto et par date
CREATE INDEX IF NOT EXISTS idx_prices_symbol 
    ON crypto_prices(symbol);

CREATE INDEX IF NOT EXISTS idx_prices_date 
    ON crypto_prices(recorded_at);

CREATE INDEX IF NOT EXISTS idx_prices_symbol_date 
    ON crypto_prices(symbol, recorded_at);

-- Vue matérialisée pour les corrélations (comme on a appris)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_prices AS
SELECT
    symbol,
    DATE(recorded_at)       AS jour,
    AVG(price_usd)          AS prix_moyen,
    MAX(price_usd)          AS prix_max,
    MIN(price_usd)          AS prix_min,
    AVG(change_24h)         AS variation_moyenne,
    AVG(volume_24h)         AS volume_moyen
FROM crypto_prices
GROUP BY symbol, DATE(recorded_at);

CREATE INDEX IF NOT EXISTS idx_mv_symbol 
    ON mv_daily_prices(symbol);

CREATE INDEX IF NOT EXISTS idx_mv_jour 
    ON mv_daily_prices(jour);