'''
import streamlit as st
import json
from backend.portfolio import Portfolio

st.set_page_config(page_title="FinSight AI", layout="wide")

st.title("📊 FinSight AI")
st.write("AI-powered portfolio analysis & insights.")

# --- Portfolio instance ---
portfolio = Portfolio()

# --- Sidebar: input portfolio ---
st.sidebar.header("Your Portfolio")
tickers_input = st.sidebar.text_area(
    "Enter holdings as TICKER:WEIGHT (comma separated)",
    value="AAPL:0.5, TSLA:0.3, GOOGL:0.2"
)

if st.sidebar.button("Load Portfolio"):
    try:
        # reset portfolio each time
        portfolio.stocks = {}
        parts = tickers_input.split(",")
        for p in parts:
            if ":" in p:
                t, w = p.split(":")
                portfolio.add_stock(t.strip(), float(w.strip()))
        st.sidebar.success("Portfolio loaded!")
    except Exception as e:
        st.sidebar.error(f"Error parsing portfolio: {e}")

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["📈 Insights", "⚠️ Risk Analysis", "📑 Report"])

with tab1:
    st.subheader("Portfolio Insights")
    if portfolio.stocks:
        try:
            insights = portfolio.ai_portfolio_insight(audience="Beginner")
            st.write(insights)
        except Exception as e:
            st.error(f"Error generating insights: {e}")
    else:
        st.info("Load a portfolio to see insights.")

with tab2:
    st.subheader("Risk Analysis")
    if portfolio.stocks:
        period = st.selectbox(
            "Select analysis period",
            ["6mo", "1y", "3y", "5y"],
            index=1  # default "1y"
        )
        if st.button("Run Risk Analysis"):
            try:
                risk = portfolio.analyze_risk(period=period)
                st.json(risk)
            except Exception as e:
                st.error(f"Error during risk analysis: {e}")
    else:
        st.info("Load a portfolio to run risk analysis.")


with tab3:
    st.subheader("Report")
    if portfolio.stocks:
        try:
            report = portfolio.generate_report()
            st.json(report)
        except Exception as e:
            st.error(f"Error generating report: {e}")
    else:
        st.info("Load a portfolio to generate a report.")
 '''
import streamlit as st
import json
from backend.portfolio import Portfolio

st.set_page_config(page_title="FinSight AI", layout="wide")

st.title("📊 FinSight AI")
st.write("AI-powered portfolio analysis & insights.")

# --- Keep portfolio persistent in session ---
if "portfolio" not in st.session_state:
    st.session_state.portfolio = Portfolio()

portfolio = st.session_state.portfolio

# --- Sidebar: input portfolio ---
st.sidebar.header("Your Portfolio")
tickers_input = st.sidebar.text_area(
    "Enter holdings as TICKER:WEIGHT (comma separated)",
    value="AAPL:0.5, TSLA:0.3, GOOGL:0.2"
)

if st.sidebar.button("Load Portfolio"):
    try:
        # reset portfolio each time
        portfolio.stocks = {}
        parts = tickers_input.split(",")
        for p in parts:
            if ":" in p:
                t, w = p.split(":")
                portfolio.add_stock(t.strip(), float(w.strip()))
        st.sidebar.success("Portfolio loaded!")
    except Exception as e:
        st.sidebar.error(f"Error parsing portfolio: {e}")

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["📈 Insights", "⚠️ Risk Analysis", "📑 Report"])

with tab1:
    st.subheader("Portfolio Insights")
    if portfolio.stocks:
        try:
            insights = portfolio.ai_portfolio_insight(audience="Beginner")
            st.write(insights)
        except Exception as e:
            st.error(f"Error generating insights: {e}")
    else:
        st.info("Load a portfolio to see insights.")

with tab2:
    st.subheader("Risk Analysis")
    if portfolio.stocks:
        period = st.selectbox(
            "Select analysis period",
            ["6mo", "1y", "3y", "5y"],
            index=1  # default "1y"
        )
        if st.button("Run Risk Analysis"):
            try:
                risk = portfolio.analyze_risk(period=period)
                st.json(risk)
            except Exception as e:
                st.error(f"Error during risk analysis: {e}")
    else:
        st.info("Load a portfolio to run risk analysis.")

with tab3:
    st.subheader("Report")
    if portfolio.stocks:
        try:
            report = portfolio.generate_report()
            st.json(report)
        except Exception as e:
            st.error(f"Error generating report: {e}")
    else:
        st.info("Load a portfolio to generate a report.")
