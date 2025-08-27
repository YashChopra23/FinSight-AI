import os
import time
import requests
import yfinance as yf
from dotenv import load_dotenv
load_dotenv()

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
ALPHA_KEY   = os.getenv("ALPHAVANTAGE_API_KEY")

def get_price_timeseries(ticker: str, period="5d", interval="1d"):
    """Historical OHLCV using yfinance (no API key needed)."""
    t = yf.Ticker(ticker)
    hist = t.history(period=period, interval=interval)
    # Convert to a compact dict for prompting/printing
    return hist.reset_index()[["Date","Open","High","Low","Close","Volume"]].tail(10)

def get_company_profile(ticker: str):
    t = yf.Ticker(ticker)
    info = t.info or {}
    return {
        "longName": info.get("longName"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "marketCap": info.get("marketCap"),
        "forwardPE": info.get("forwardPE"),
        "beta": info.get("beta"),
    }

def get_latest_news(query: str, page_size=5):
    """Uses NewsAPI if key present, otherwise returns empty list."""
    if not NEWSAPI_KEY:
        return []
    url = ("https://newsapi.org/v2/everything?"
           f"q={requests.utils.quote(query)}&language=en&sortBy=publishedAt&pageSize={page_size}")
    r = requests.get(url, headers={"X-Api-Key": NEWSAPI_KEY}, timeout=20)
    r.raise_for_status()
    articles = r.json().get("articles", [])
    # Compact representation
    return [{
        "title": a.get("title"),
        "source": a.get("source", {}).get("name"),
        "publishedAt": a.get("publishedAt"),
        "url": a.get("url"),
        "description": a.get("description")
    } for a in articles]
