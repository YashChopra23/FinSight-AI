# llm.py
import os
from dotenv import load_dotenv
import google.generativeai as genai

# --- Setup ---
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = "gemini-1.5-flash"

# --- 1. Stock-level summarization ---
def summarize_market(ticker, profile, prices_df, news_list, audience="Beginner"):
    """Combine structured data + news into a single Gemini summary."""
    prices_text = prices_df.to_csv(index=False)

    tone = ("Explain like I’m new to markets, avoid jargon."
            if audience.lower().startswith("begin") else
            "Use concise analyst tone with key metrics and risks.")

    prompt = f"""
You are a market analyst. Summarize the current situation for {ticker}.
Company profile: {profile}

Recent OHLCV (CSV):
{prices_text}

Latest news headlines:
{news_list}

Requirements:
- {tone}
- Include 2–3 key takeaways.
- Mention notable price moves (up/down days) if visible.
- If news_list is empty, say no fresh headlines found.
- End with a one-sentence risk or watch-out.
"""
    model = genai.GenerativeModel(MODEL_NAME)
    res = model.generate_content(prompt)
    return res.text.strip()

# --- 2. Generic summarizer wrapper ---
def ai_summary(prompt: str) -> str:
    """Simple wrapper to generate a short summary (used for portfolio insights)."""
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        res = model.generate_content(prompt)
        return res.text.strip()
    except Exception as e:
        return (
            "Portfolio insight unavailable: AI service not configured. "
            "Please set GEMINI_API_KEY."
        )
