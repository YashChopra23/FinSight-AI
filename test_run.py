from backend.portfolio import Portfolio

def main():
    p = Portfolio()
    p.add_stock("AAPL")
    p.add_stock("TSLA")

    print("\n=== AI Portfolio Insight ===")
    print(p.ai_portfolio_insight(audience="Beginner"))

if __name__ == "__main__":
    main()
