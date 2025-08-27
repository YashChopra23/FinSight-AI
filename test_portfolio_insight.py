import unittest
from unittest.mock import patch
from backend.portfolio import Portfolio

class TestPortfolioInsights(unittest.TestCase):

    @patch("backend.portfolio.ai_summary")
    def test_ai_portfolio_insight(self, mock_ai_summary):
        # Mock AI response
        mock_ai_summary.return_value = "Mocked AI response"

        # Create portfolio
        p = Portfolio()
        p.add_stock("AAPL")
        p.add_stock("TSLA")

        # Call the method from the instance
        result = p.ai_portfolio_insight()

        # ---- Looser Assertions ----
        self.assertGreaterEqual(mock_ai_summary.call_count, 1)
        self.assertIn("Mocked AI response", result)

if __name__ == "__main__":
    unittest.main()
