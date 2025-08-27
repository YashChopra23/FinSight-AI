from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator
from typing import Dict, Optional
import logging
import os
from dotenv import load_dotenv

from backend.portfolio import Portfolio  # your Portfolio class

# -------------------- Config & Logging --------------------
load_dotenv()  # load .env variables
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("finsight-ai")

app = FastAPI(title="FinSight-AI API")

# -------------------- Request Models --------------------

class PortfolioRequest(BaseModel):
    portfolio: Dict[str, float]  # ticker + weight

    @validator("portfolio")
    def validate_weights(cls, v):
        total = sum(v.values())
        if total <= 0:
            raise ValueError("Portfolio weights must be positive")
        if abs(total - 1.0) > 1e-6:
            raise ValueError("Portfolio weights must sum to 1.0")
        return v


class RiskAnalysisRequest(PortfolioRequest):
    period: str = "3mo"   # default period
    # you could validate period format if needed


class ReportRequest(PortfolioRequest):
    period: Optional[str] = "6mo"  # optional period for reports


# -------------------- Endpoints --------------------

@app.get("/")
def root():
    return {"message": "Welcome to FinSight-AI Backend"}


@app.post("/portfolio-insight", tags=["Insights"], summary="Get AI-generated portfolio insights")
def get_insights(request: PortfolioRequest):
    try:
        logger.info(f"Generating insights for portfolio: {request.portfolio}")
        p = Portfolio()
        for ticker, weight in request.portfolio.items():
            p.add_stock(ticker, weight)

        insights = p.ai_portfolio_insight()
        return {"insights": insights}
    except Exception as e:
        logger.error(f"Portfolio insight failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate portfolio insights")


@app.post("/risk-analysis", tags=["Analysis"], summary="Run portfolio risk analysis")
def risk_analysis(request: RiskAnalysisRequest):
    try:
        logger.info(f"Risk analysis for: {request.portfolio}, period={request.period}")
        p = Portfolio()
        for ticker, weight in request.portfolio.items():
            p.add_stock(ticker, weight)

        risk = p.analyze_risk(period=request.period)
        return {"risk": risk}
    except Exception as e:
        logger.error(f"Risk analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Risk analysis failed")


@app.post("/report", tags=["Reports"], summary="Generate portfolio report")
def generate_report(request: ReportRequest):
    try:
        logger.info(f"Generating report for: {request.portfolio}")
        p = Portfolio()
        for ticker, weight in request.portfolio.items():
            p.add_stock(ticker, weight)

        report = p.generate_report()
        return {"report": report}
    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Report generation failed")
