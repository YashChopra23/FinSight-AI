# backend/portfolio.py
import math
from typing import Dict, List, Tuple
import yfinance as yf
import pandas as pd

from backend.llm import ai_summary  # uses your wrapper in llm.py

class Portfolio:
    """
    Minimal portfolio manager that:
    - Stores tickers
    - Pulls basic fundamentals (name, sector, marketCap)
    - Computes sector breakdown (cap-weighted if available, else equal-weight)
    - Computes simple volatilities from recent prices
    - Produces a portfolio-level AI insight (using Gemini)
    """
    def __init__(self):
        self.stocks = {}

    # ---- CRUD ----
    def add_stock(self, ticker: str, weight: float = 1.0) -> str:
        ticker = ticker.upper().strip()
        if ticker and ticker not in self.stocks:
            self.stocks[ticker]=weight
            return f"{ticker} added to portfolio."
        return f"{ticker} already exists."

    def remove_stock(self, ticker: str) -> str:
        ticker = ticker.upper().strip()
        if ticker in self.stocks:
            del self.stocks[ticker]
            return f"{ticker} removed from portfolio."
        return f"{ticker} not found in portfolio."

    # ---- Data pulls ----
    def _fetch_info(self, ticker: str) -> Dict:
        try:
            return yf.Ticker(ticker).info or {}
        except Exception:
            return {}

    def _fetch_history(self, ticker: str, period: str = "3mo") -> pd.DataFrame:
        try:
            df = yf.Ticker(ticker).history(period=period, interval="1d")
            if isinstance(df, pd.DataFrame) and not df.empty:
                df = df.reset_index()
            return df
        except Exception:
            return pd.DataFrame()

    # ---- Snapshots ----
    def get_portfolio_data(self) -> Dict[str, Dict]:
        data = {}
        for t in self.stocks:
            info = self._fetch_info(t)
            data[t] = {
                "name": info.get("longName", "N/A"),
                "sector": info.get("sector", "Unknown"),
                "marketCap": info.get("marketCap", 0) or 0,
                "forwardPE": info.get("forwardPE", None),
                # quick blurb per stock (reuses your ai_summary wrapper)
                "summary": ai_summary(f"Give a brief non-advisory stock overview for {t}.")
            }
        return data

    # ---- Analytics ----
    def sector_breakdown(self) -> List[Tuple[str, float]]:
        """
        Returns list of (sector, weight_pct) sorted desc.
        Uses marketCap for weights when available, otherwise equal-weight.
        """
        if not self.stocks:
            return []

        # collect sectors + caps
        sector_weights: Dict[str, float] = {}
        for t,w in self.stocks.items():
            info = self._fetch_info(t)
            sector = info.get("sector", "Unknown")
            sector_weights[sector] = sector_weights.get(sector, 0.0) + float(w)
        breakdown = [(s, pct * 100.0) for s, pct in sector_weights.items()]
        breakdown.sort(key=lambda x: x[1], reverse=True)
        return breakdown   

        

    def ticker_volatilities(self, period: str = "3mo") -> Dict[str, float]:
        """
        Annualized volatility per ticker using daily Close returns.
        """
        vols: Dict[str, float] = {}
        for t in self.stocks:
            hist = self._fetch_history(t, period=period)
            if hist is None or hist.empty or "Close" not in hist.columns:
                vols[t] = float("nan")
                continue
            ret = hist["Close"].pct_change().dropna()
            if ret.empty:
                vols[t] = float("nan")
                continue
            daily_std = float(ret.std())
            ann_vol = daily_std * math.sqrt(252.0)
            vols[t] = ann_vol
        return vols

    def portfolio_volatility(self, period: str = "3mo") -> float:
        """
        Equal-weight portfolio annualized volatility (simple).
        """
        if not self.stocks:
            return float("nan")
        # Build return DataFrame
        rets = []
        for t in self.stocks:
            h = self._fetch_history(t, period=period)
            if h is None or h.empty or "Close" not in h.columns:
                continue
            r = h[["Date", "Close"]].copy()
            r[t] = r["Close"].pct_change()
            r = r.dropna()[["Date", t]]
            rets.append(r.set_index("Date"))
        if not rets:
            return float("nan")
        R = pd.concat(rets, axis=1).dropna()
        if R.empty:
            return float("nan")
        # normalize weights
        weights = pd.Series(self.stocks, index=R.columns, dtype=float)
        weights = weights / weights.sum()
        
        # portfolio return = weighted sum of daily returns
        port_ret = R.mul(weights, axis=1).sum(axis=1)
        ann_vol = float(port_ret.std() * math.sqrt(252.0))
        return ann_vol
    def volatility(self, ticker: str, period: str = "3mo") -> float:
        return self.ticker_volatilities(period).get(ticker, float("nan"))


    # ---- AI Insight ----
    def ai_portfolio_insight(self, audience: str = "Beginner") -> str:
        
        """
        LLM summary of portfolio composition + risks.
        """
        if not self.stocks:
            return "Portfolio is empty. Add some tickers first."

        # gather basics
        data = self.get_portfolio_data()
        sectors = self.sector_breakdown()
        vols = self.ticker_volatilities()
        pvol = self.portfolio_volatility()

        # simple flags
        top_sector = sectors[0] if sectors else ("Unknown", 0)
        concentration_flag = (top_sector[1] >= 60.0)
        high_vol_names = [t for t, v in vols.items() if isinstance(v, float) and v >= 0.40]

        # diversification score
        if concentration_flag:
            diversification_score = "Poor"
        elif len(sectors) < 3:
            diversification_score = "Moderate"
        else:
            diversification_score = "Good"

        # risk classification (based on vol + diversification)
        if pvol != pvol:  # NaN check
            risk_level, risk_score = "Unknown", "N/A"
        else:
            if pvol > 0.40:
                risk_level, risk_score = "High", 80
            elif pvol > 0.20:
                risk_level, risk_score = "Moderate", 50
            else:
                risk_level, risk_score = "Low", 20

            # adjust by diversification
            if diversification_score == "Poor":
                risk_score = min(100, risk_score + 20)
                risk_level = "High"
            elif diversification_score == "Moderate":
                risk_score = min(100, risk_score + 10)

        # build a compact context for the LLM
        basics = []
        for t, info in data.items():
            basics.append({
                "ticker": t,
                "name": info.get("name", "N/A"),
                "sector": info.get("sector", "Unknown"),
                "mcap": info.get("marketCap", 0)
            })

        prompt = f"""
    You are a portfolio analyst. Provide a concise, non-advisory overview.

    Portfolio:
    - Tickers: {list(self.stocks.keys())}
    - Weights: {self.stocks}
    - Holdings: {basics}
    - Sector mix (%): {sectors}
    - Annualized volatility (3mo): {round(pvol, 3) if pvol == pvol else "N/A"}
    - Diversification: {diversification_score}
    - Risk Classification: {risk_level} (score {risk_score}/100)

    Flags:
    - Sector concentration >=60%? {concentration_flag} (top sector: {top_sector})
    - High-vol stocks (>=40% ann vol): {high_vol_names}

    Audience: {audience}

    Requirements:
    - Start with one-sentence summary (tilt + risk).
    - Then 4–5 bullets with specifics:
    • Sector concentration (if flagged).
    • High-vol stocks and their effect.
    • Portfolio risk classification.
    • Diversification assessment.
    • 1–2 de-risking categories (e.g., “add defensive sectors”), no stock picks.
    - End with a single caveat: this is NOT financial advice.
    """
        return ai_summary(prompt)

    def analyze_risk(self, period: str = "3mo") -> Dict:
        """
        Builds a portfolio-level risk snapshot using existing methods.
        """
        if not self.stocks:
            return {"error": "Portfolio is empty."}

        vols = self.ticker_volatilities(period)
        pvol = self.portfolio_volatility(period)
        sectors = self.sector_breakdown()

        top_sector = sectors[0] if sectors else ("Unknown", 0)
        concentration_flag = (top_sector[1] >= 60.0)
        high_vol_names = [t for t, v in vols.items() if isinstance(v, float) and v >= 0.40]

        return {
            "portfolio_volatility": round(pvol, 3) if pvol == pvol else None,
            "sector_concentration": {
                "flagged": concentration_flag,
                "top_sector": top_sector,
            },
            "high_vol_stocks": high_vol_names,
            "ticker_volatilities": vols,
        }

    def generate_report(self, audience: str = "Beginner") -> Dict:
        """
        Generates a portfolio summary (data + AI insight).
        """
        if not self.stocks:
            return {"error": "Portfolio is empty."}

        return {
            "holdings": self.get_portfolio_data(),
            "sectors": self.sector_breakdown(),
            "portfolio_volatility": self.portfolio_volatility(),
            "ai_summary": self.ai_portfolio_insight(audience),
        }

