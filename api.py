import os
from fastapi import FastAPI
# Pour les erreurs HTTP
from fastapi import HTTPException
# Connexion PostgreSQL — réutilise ce que tu as dans analyzer.py
from sqlalchemy import create_engine
import pandas as pd
from sqlalchemy import text

from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

VALID_SYMBOLS = ['BTC', 'ETH', 'BNB', 'SOL']

@app.get("/")
def root():
    return {"name": "CryptoCompare API", 
            "version": "1.0.0"
    }
    
@app.get("/cryptos")
def get_cryptos():
        return {"cryptos": VALID_SYMBOLS}

def get_engine():
        database_url = os.getenv("DATABASE_URL")
        if database_url:
                # Railway fournit une URL complète
                return create_engine(database_url)
        else:
                # Environnement local
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

@app.get("/prices/{symbol}")
def get_prices(symbol: str, days: int = 30):
        symbol = symbol.upper()
        
        if symbol not in VALID_SYMBOLS:
                raise HTTPException(
                        status_code=400, 
                        detail=f"Symbole invalide. Disponibles : {VALID_SYMBOLS}"
                )
        df = run_query("""
                SELECT jour, prix_moyen, prix_max, prix_min, volume_moyen
                FROM mv_daily_prices
                WHERE symbol = %(symbol)s
                ORDER BY jour DESC
                LIMIT %(days)s
        """, params={"symbol": symbol, "days": days})
           
        return {
        "symbol": symbol,
        "days": days,
        "data": df.to_dict(orient="records")
        }
        
@app.get("/correlation/{symbol_a}/{symbol_b}")
def get_correlation(symbol_a: str, symbol_b: str):
        
        symbol_a = symbol_a.upper()
        symbol_b = symbol_b.upper()
        
        if symbol_a not in VALID_SYMBOLS or symbol_b not in VALID_SYMBOLS:
                raise HTTPException(
                        status_code=400, 
                        detail=f"Symboles invalides. Disponibles : {VALID_SYMBOLS}"
                )
        if symbol_a == symbol_b:
                raise HTTPException(
                        status_code=400, 
                        detail="Les symboles doivent être différents."
                )
        df = run_query("""
        SELECT ROUND(corr(a.prix_moyen, b.prix_moyen)::numeric, 4) as correlation
        FROM mv_daily_prices a
        JOIN mv_daily_prices b ON a.jour = b.jour
        WHERE a.symbol = %(symbol_a)s
        AND b.symbol = %(symbol_b)s
        """, params={"symbol_a": symbol_a, "symbol_b": symbol_b})

        return {
        "pair": f"{symbol_a}/{symbol_b}",
        "correlation": float(df.iloc[0, 0]) if not df.empty else None
        }
    
@app.get("/volatility")
def get_volatility():
        df = run_query("""
                SELECT symbol, jour, prix_moyen
                FROM mv_daily_prices
                ORDER BY symbol, jour
        """)
        
        results = []
        for symbol in VALID_SYMBOLS:
                data = df[df['symbol'] == symbol].copy()
                data = data.sort_values('jour')
                data['variation'] = data['prix_moyen'].pct_change() * 100

                results.append({
                "symbol": symbol,
                "volatilite_pct": round(float(data['variation'].std()), 4),
                "variation_moyenne_pct": round(float(data['variation'].mean()), 4),
                "prix_max": round(float(data['prix_moyen'].max()), 2),
                "prix_min": round(float(data['prix_moyen'].min()), 2)
                })

        results.sort(key=lambda x: x['volatilite_pct'], reverse=True)
        return {"volatility": results}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("api:app", host="0.0.0.0", port=port)