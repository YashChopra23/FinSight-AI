import pytest
import pandas as pd
from backend.portfolio import Portfolio

def test_add_and_sector_breakdown():
    p = Portfolio()
    p.add_stock("AAPL")
    p.add_stock("MSFT")

    sectors = p.sector_breakdown()
    assert isinstance(sectors, list)
    assert all(isinstance(s, tuple) and len(s) == 2 for s in sectors)
    assert any("Technology" in s for s in sectors)

def test_volatility_calculation():
    p = Portfolio()
    p.add_stock("AAPL")
    vol = p.volatility("AAPL")
    assert isinstance(vol, float)
    assert vol > 0  # volatility should be positive

def test_portfolio_volatility():
    p = Portfolio()
    p.add_stock("AAPL")
    p.add_stock("MSFT")
    vol = p.portfolio_volatility()
    assert isinstance(vol, float)
    assert vol > 0

def test_ai_portfolio_insight():
    p = Portfolio()
    p.add_stock("AAPL")
    p.add_stock("MSFT")
    insight = p.ai_portfolio_insight()
    assert isinstance(insight, str)
    assert "portfolio" in insight.lower()
