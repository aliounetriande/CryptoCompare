# CryptoCompare

A REST API that analyzes correlations between cryptocurrencies using real market data from CoinGecko.

## What it does
- Fetches 90 days of historical price data for BTC, ETH, BNB, SOL
- Stores data in PostgreSQL for analysis
- Computes Pearson correlation between any two cryptos
- Measures volatility and 90-day performance
- Exposes all analysis via a FastAPI REST API

## Tech Stack
Language       | Python 3.12
API Framework  | FastAPI + Uvicorn
Database       | PostgreSQL 16
ORM / Queries  | SQLAlchemy + pandas
Data Source    | CoinGecko API (free)
Infrastructure | Docker + Docker Compose


## API Endpoints
- GET | `/` | API info
- GET | `/cryptos` | List available cryptos
- GET | `/prices/{symbol}?days=30` | Historical prices for a crypto |
- GET | `/correlation/{symbol_a}/{symbol_b}` | Pearson correlation between two cryptos
- GET | `/volatility` | Volatility ranking of all cryptos

## Run locally
**Prerequisites:** Python 3.12, PostgreSQL 16, pip

```bash
git clone https://github.com/your-username/cryptocompare.git
cd cryptocompare

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your DB credentials

# Collect data
python main.py collect

# Start API
uvicorn api:app --reload --port 8000
```

API docs available at: `http://localhost:8000/docs`

## Run with Docker

```bash
git clone https://github.com/your-username/cryptocompare.git
cd cryptocompare

docker compose up --build -d

# Collect data into Docker PostgreSQL
DB_HOST=localhost DB_PORT=5435 DB_NAME=cryptocompare \
DB_USER=postgres DB_PASSWORD=postgres \
python main.py collect

# Refresh materialized view
docker exec $(docker compose ps -q postgres) \
  psql -U postgres -d cryptocompare \
  -c "REFRESH MATERIALIZED VIEW mv_daily_prices;"
```

API docs available at: `http://localhost:8000/docs`

## License

MIT