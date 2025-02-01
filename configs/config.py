# configs/config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# API Keys loaded from environment variables
X_API_KEY = os.getenv("X_API_KEY")
DEXS_API_KEY = os.getenv("DEXS_API_KEY")

# API Endpoints (replace with actual endpoints as needed)
X_ENDPOINT = "https://api.x.com/endpoint"  # Example: Replace with the actual X.com API endpoint
DEXS_ENDPOINT = os.getenv("DEXS_ENDPOINT", "https://api.dexscreener.com/latest/dex")

# Default Parameters
DEFAULT_SENTIMENT_THRESHOLD = 0.5
