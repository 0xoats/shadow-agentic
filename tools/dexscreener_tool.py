import json
import os
import requests
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage

load_dotenv()

from configs.config import DEXS_ENDPOINT

class DexscreenerTool:
    def __init__(self):
        # Base endpoint for the Dexscreener API (e.g., "https://api.dexscreener.com/latest/dex")
        self.endpoint = DEXS_ENDPOINT
        self.model = ChatOpenAI(model="gpt-4o")
        self.coingecko_base_url = "https://api.coingecko.com/api/v3"
        # We'll cache top coin data so we don't repeatedly fetch from CoinGecko
        self._coins_cache = []

    def _fetch_coingecko_coins(self, limit: int = 250) -> list:
        """
        Fetch a list of top tokens by market cap from CoinGecko using '/coins/markets'.
        Returns a list of dictionaries like:
          [
            {
              "id": "ethereum",
              "symbol": "eth",
              "name": "Ethereum",
              "market_cap": 1234567890,
              "total_volume": 987654321,
              ...
            },
            ...
          ]
        """
        url = f"{self.coingecko_base_url}/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": limit,
            "page": 1,
            "sparkline": "false"
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data  # List of coin dicts
        except Exception as e:
            print(f"Error fetching top coins from CoinGecko: {e}")
            return []

    def _ensure_coins_cache(self):
        """
        Load coin data into self._coins_cache if empty.
        """
        if not self._coins_cache:
            self._coins_cache = self._fetch_coingecko_coins(limit=300)

    def get_volume_mcap_ratio(self, symbol: str) -> float:
        """
        Return the 24h volume / market cap ratio for a given token symbol
        from the cached coin data. If not found or invalid, returns 0.0.
        """
        self._ensure_coins_cache()
        symbol_lower = symbol.lower()

        for coin in self._coins_cache:
            if coin.get("symbol", "").lower() == symbol_lower:
                market_cap = coin.get("market_cap", 0) or 0
                total_volume = coin.get("total_volume", 0) or 0

                if market_cap > 0:
                    return float(total_volume) / float(market_cap)
                else:
                    return 0.0
        return 0.0

    def find_tokens_with_similar_ratio(self, base_ratio: float, threshold: float = 0.2) -> list:
        """
        Find tokens whose (24h volume / market cap) ratio is within 
        +/- (threshold * 100)% of 'base_ratio'.
        
        threshold=0.2 => +/- 20%
        Returns a list of token symbols (in uppercase).
        """
        self._ensure_coins_cache()
        lower_bound = base_ratio * (1 - threshold)
        upper_bound = base_ratio * (1 + threshold)

        similar_tokens = []
        for coin in self._coins_cache:
            mcap = coin.get("market_cap", 0) or 0
            volume = coin.get("total_volume", 0) or 0

            if mcap <= 0:
                continue

            ratio = volume / mcap
            if lower_bound <= ratio <= upper_bound:
                similar_tokens.append(coin["symbol"].upper())

        return similar_tokens

    def analyze_similar_tokens(self, wallet_insights: dict) -> dict:
        """
        1) Extract tokens from 'wallet_insights'.
        2) Compute each token's volume/mcap ratio.
        3) Find tokens with a similar ratio.
        4) For each similar token, pull Dexscreener data.
        5) (Optional) Use an LLM to provide technical analysis.
        
        Returns:
          {
            "similar_tokens_analysis": {
              "<TOKEN_SYMBOL>": { "raw_data": ... },
              ...
            },
            "tokens_examined": ["TOKEN1", "TOKEN2", ...]
          }
        """
        tokens_bought = wallet_insights.get("tokens_bought", [])
        # 1) Calculate each token's ratio
        token_ratios = {}
        for symbol in tokens_bought:
            ratio = self.get_volume_mcap_ratio(symbol)
            token_ratios[symbol.upper()] = ratio

        # 2) For each token, find tokens with similar ratio
        tokens_of_interest = set()
        for symbol, ratio in token_ratios.items():
            if ratio > 0:
                similar = self.find_tokens_with_similar_ratio(ratio, threshold=0.2)
                tokens_of_interest.update(similar)

        tokens_of_interest = list(tokens_of_interest)
        
        # Fallback if we didn't get any
        if not tokens_of_interest:
            tokens_of_interest = ["ETH", "BTC", "SOL", "ADA"]

        similar_tokens_analysis = {}

        # 3) For each similar token, fetch Dexscreener data (first pair only, for brevity)
        for token in tokens_of_interest:
            search_url = f"{self.endpoint}/search"
            params = {"q": token}
            try:
                response = requests.get(search_url, params=params, timeout=10)
                if response.status_code != 200:
                    similar_tokens_analysis[token] = {
                        "error": f"Error searching for token '{token}': {response.text}"
                    }
                    continue
            except Exception as e:
                similar_tokens_analysis[token] = {
                    "error": f"Network error searching token '{token}': {str(e)}"
                }
                continue

            search_data = response.json()
            pairs = search_data.get("pairs", [])
            if not pairs:
                similar_tokens_analysis[token] = {
                    "error": f"No pairs found for token '{token}'."
                }
                continue

            pair_data = pairs[0]

            # Step 2: Prepare a prompt to analyze the technical data for this token pair.
            prompt = (
                f"Below is raw data from Dexscreener for a token pair related to {token}. "
                "Please analyze the data and provide technical insights, including trend, volatility, and key indicators.\n\n"
                f"{json.dumps(pair_data, indent=2)}"
            )

            chat_history = []
            system_message = SystemMessage(
                content="You are a skilled market analyst with expertise in crypto technical analysis."
            )
            chat_history.append(system_message)
            chat_history.append(HumanMessage(content=prompt))

            result = self.model.invoke(chat_history)
            analysis = result.content

            similar_tokens_analysis[token] = {
                "technical_analysis": analysis,
                "raw_data": pair_data
            }

        return {
            "similar_tokens_analysis": similar_tokens_analysis,
            "tokens_examined": list(token_ratios.keys())
        }

    def get_technical_analysis(self, token_symbol: str) -> dict:
        """
        (Optional) Retrieve Dexscreener data for a single token, then do LLM analysis if desired.
        """
        search_url = f"{self.endpoint}/search"
        params = {"q": token_symbol}
        try:
            response = requests.get(search_url, params=params, timeout=10)
            response.raise_for_status()
        except Exception as e:
            raise Exception(f"Error searching for token '{token_symbol}': {str(e)}")

        search_data = response.json()
        pairs = search_data.get("pairs", [])
        if not pairs:
            raise Exception(f"No pairs found for token '{token_symbol}'.")

        pair_data = pairs[0]

        prompt = (
            f"Below is raw data from Dexscreener for a token pair related to {token_symbol}. "
            "Please analyze the data and provide technical insights, including trend, volatility, and key indicators.\n\n"
            f"{json.dumps(pair_data, indent=2)}"
        )

        chat_history = []
        # TODO: Refine the prompt
        system_message = SystemMessage(
            content="You are a skilled market analyst with expertise in crypto technical analysis."
        )
        chat_history.append(system_message)
        chat_history.append(HumanMessage(content=prompt))

        result = self.model.invoke(chat_history)
        analysis = result.content

        return {
            "token": token_symbol,
            "technical_analysis": analysis,
            "raw_data": pair_data
        }
