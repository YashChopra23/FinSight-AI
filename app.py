import streamlit as st
import json
import pandas as pd
import plotly.express as px
from typing import List, Dict
from backend.portfolio import Portfolio

st.set_page_config(page_title="FinSight AI", page_icon="📊", layout="wide")

# ---- Minimal styling ----
st.markdown(
    """
    <style>
      .finsight-hero h1 {margin-bottom: 0rem}
      .finsight-hero p {color: #888; margin-top: 0.25rem}
      .chip {display:inline-block; padding:4px 10px; border-radius:999px; font-size:12px; margin-right:6px; background: rgba(0,0,0,0.06)}
      .chip.flag {background:#FFE8E8; color:#B00020}
      .chip.ok {background:#E6F4EA; color:#137333}
      .markdown-insight {padding: 0.75rem 1rem; border-radius: 10px; background: var(--secondary-background-color, #f6f6f6);}
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Keep portfolio persistent in session ---
if "portfolio" not in st.session_state:
    st.session_state.portfolio = Portfolio()

portfolio: Portfolio = st.session_state.portfolio

# --- Sidebar: Portfolio builder ---
st.sidebar.header("Portfolio Builder")

sample_portfolios: Dict[str, List[Dict[str, float]]] = {
    "Tech Growth": [
        {"Ticker": "AAPL", "Weight": 0.40},
        {"Ticker": "MSFT", "Weight": 0.30},
        {"Ticker": "NVDA", "Weight": 0.20},
        {"Ticker": "GOOGL", "Weight": 0.10},
    ],
    "Balanced ETFs": [
        {"Ticker": "SPY", "Weight": 0.60},
        {"Ticker": "AGG", "Weight": 0.30},
        {"Ticker": "GLD", "Weight": 0.10},
    ],
    "Blue Chips": [
        {"Ticker": "KO", "Weight": 0.25},
        {"Ticker": "PG", "Weight": 0.25},
        {"Ticker": "JNJ", "Weight": 0.25},
        {"Ticker": "JPM", "Weight": 0.25},
    ],
}

chosen_sample = st.sidebar.selectbox("Sample portfolios", list(sample_portfolios.keys()), index=0)
if st.sidebar.button("Use sample"):
    df_sample = pd.DataFrame(sample_portfolios[chosen_sample])
else:
    # default editor state from current portfolio
    df_sample = pd.DataFrame(
        [{"Ticker": t, "Weight": float(w)} for t, w in portfolio.stocks.items()] or
        [{"Ticker": "AAPL", "Weight": 0.50}, {"Ticker": "TSLA", "Weight": 0.30}, {"Ticker": "GOOGL", "Weight": 0.20}]
    )

st.sidebar.caption("Tip: weights do not need to sum to 1; we normalize when needed.")
edit_df = st.sidebar.data_editor(
    df_sample,
    key="portfolio_editor",
    use_container_width=True,
    num_rows="dynamic",
    column_config={
        "Ticker": st.column_config.TextColumn(help="Ticker symbol (e.g., AAPL)"),
        "Weight": st.column_config.NumberColumn(format="%0.2f", min_value=0.0),
    },
)

if st.sidebar.button("Apply portfolio"):
    try:
        portfolio.stocks = {}
        for _, row in edit_df.dropna().iterrows():
            t = str(row.get("Ticker", "")).strip()
            w = float(row.get("Weight", 0.0) or 0.0)
            if t:
                portfolio.add_stock(t, w)
        st.sidebar.success("Portfolio applied ✅")
    except Exception as e:
        st.sidebar.error(f"Failed to apply portfolio: {e}")

# ---- Hero ----
st.markdown("<div class='finsight-hero'>", unsafe_allow_html=True)
st.title("FinSight AI")
st.write("AI-powered portfolio insights, risk, and reports.")
st.markdown("</div>", unsafe_allow_html=True)

has_positions = bool(portfolio.stocks)

def compute_diversification_text(breakdown: List):
    if not breakdown:
        return "Unknown"
    top = breakdown[0][1]
    if top >= 60.0:
        return "Poor"
    if len(breakdown) < 3:
        return "Moderate"
    return "Good"

# ---- Top KPIs ----
col_k1, col_k2, col_k3, col_k4 = st.columns(4)
if has_positions:
    sectors = portfolio.sector_breakdown()
    pvol = portfolio.portfolio_volatility()
    num_holdings = len(portfolio.stocks)
    top_sector = sectors[0][0] if sectors else "Unknown"
    diversification = compute_diversification_text(sectors)
    col_k1.metric("Holdings", num_holdings)
    col_k2.metric("Top sector", top_sector)
    col_k3.metric("Diversification", diversification)
    col_k4.metric("Ann. volatility (3mo)", f"{pvol:.2f}" if pvol == pvol else "N/A")
else:
    col_k1.metric("Holdings", 0)
    col_k2.metric("Top sector", "-")
    col_k3.metric("Diversification", "-")
    col_k4.metric("Ann. volatility (3mo)", "-")

# ---- Tabs ----
tab_overview, tab_risk, tab_report = st.tabs(["📈 Overview", "⚠️ Risk", "📑 Report"])

with tab_overview:
    st.subheader("Composition and Insights")
    if not has_positions:
        st.info("Add positions in the sidebar to get started.")
    else:
        c1, c2 = st.columns([1, 1])
        # Sector pie
        sectors = portfolio.sector_breakdown()
        if sectors:
            df_sect = pd.DataFrame(sectors, columns=["Sector", "Weight %"])
            fig_pie = px.pie(df_sect, names="Sector", values="Weight %", title="Sector breakdown")
            c1.plotly_chart(fig_pie, use_container_width=True)
        # Volatility bars
        vols = portfolio.ticker_volatilities()
        if vols:
            df_vol = pd.DataFrame([
                {"Ticker": t, "Ann. Volatility": v} for t, v in vols.items()
            ])
            df_vol = df_vol.sort_values("Ann. Volatility", ascending=False)
            fig_bar = px.bar(df_vol, x="Ticker", y="Ann. Volatility", title="Ticker volatilities (ann.)")
            c2.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("---")
        st.subheader("AI Portfolio Insight")
        with st.spinner("Generating insight..."):
            insight_text = portfolio.ai_portfolio_insight(audience="Beginner")
        st.markdown(f"<div class='markdown-insight'>{insight_text}</div>", unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("Holdings snapshot")
        data = portfolio.get_portfolio_data()
        df_hold = pd.DataFrame([
            {
                "Ticker": t,
                "Name": d.get("name"),
                "Sector": d.get("sector"),
                "Market Cap": d.get("marketCap"),
                "Forward PE": d.get("forwardPE"),
            }
            for t, d in data.items()
        ])
        st.dataframe(df_hold, use_container_width=True, hide_index=True)

with tab_risk:
    st.subheader("Risk analysis")
    if not has_positions:
        st.info("Add positions in the sidebar to analyze risk.")
    else:
        period = st.selectbox("Period", ["3mo", "6mo", "1y", "3y"], index=0)
        run = st.button("Run analysis")
        if run:
            with st.spinner("Computing risk metrics..."):
                risk = portfolio.analyze_risk(period=period)
            pv = risk.get("portfolio_volatility")
            sect = risk.get("sector_concentration", {})
            flagged = sect.get("flagged")
            high_vol = risk.get("high_vol_stocks", [])

            c1, c2 = st.columns(2)
            c1.metric("Portfolio volatility", pv if pv is not None else "N/A")
            chips = []
            chips.append(f"<span class='chip {'flag' if flagged else 'ok'}'>Sector concentration: {'High' if flagged else 'OK'}</span>")
            if high_vol:
                chips.append(f"<span class='chip flag'>High-vol tickers: {', '.join(high_vol)}</span>")
            st.markdown(" ".join(chips), unsafe_allow_html=True)

            with st.expander("Details"):
                st.json(risk)

with tab_report:
    st.subheader("Report")
    if not has_positions:
        st.info("Add positions to generate a report.")
    else:
        with st.spinner("Generating report..."):
            report = portfolio.generate_report()

        st.write("AI summary:")
        st.markdown(f"<div class='markdown-insight'>{report.get('ai_summary','')}</div>", unsafe_allow_html=True)

        report_json = json.dumps(report, indent=2, default=str)
        st.download_button("Download JSON", report_json, file_name="finsight_report.json", mime="application/json")

        # Simple markdown export
        md_lines = [
            "# FinSight AI Report",
            "",
            "## AI Summary",
            report.get("ai_summary", ""),
            "",
            "## Sector Breakdown",
        ]
        for s, w in report.get("sectors", []):
            md_lines.append(f"- {s}: {w:.1f}%")
        md_lines.extend([
            "",
            "## Portfolio Volatility",
            str(report.get("portfolio_volatility")),
        ])
        md_blob = "\n".join(md_lines)
        st.download_button("Download Markdown", md_blob, file_name="finsight_report.md", mime="text/markdown")

