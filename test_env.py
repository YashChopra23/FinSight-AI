from dotenv import load_dotenv
import os

load_dotenv()
print("Gemini key loaded?", bool(os.getenv("GEMINI_API_KEY")))
